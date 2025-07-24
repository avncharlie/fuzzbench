ARG parent_image

# Build afl-dyninst on clean ubuntu 20.04 (doesn't build on parent image)
FROM ubuntu:20.04 AS afl-dyninst 

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -y upgrade && apt-get -y install \
        build-essential \
        gcc \
        g++ \
        make \
        cmake \
        git \
        gdb \
        ca-certificates \
        tar \
        gzip \
        vim \
        joe \
        wget \
        curl \
        bzip2 \
        apt-utils \
        libiberty-dev \
        libboost-all-dev \
        libdw-dev \
        libtbb2 \
        libtbb-dev \
        pkg-config \
        libcurl4-openssl-dev \
        cmake                   \
        libboost-atomic-dev     \
        libboost-chrono-dev     \
        libboost-date-time-dev  \
        libboost-filesystem-dev \
        libboost-thread-dev     \
        libboost-timer-dev      \
        libtbb-dev              \
        gettext                 \
        bzip2                   \
        zlib1g-dev              \
        m4                      \
        libiberty-dev           \
        pkg-config              \
        clang                   \
        libomp-dev \
        checkinstall \
    && apt-get -y autoremove && rm -rf /var/lib/apt/lists/*

# Install version of elfutils needed for dyninst (and generate .deb package)
RUN wget https://sourceware.org/elfutils/ftp/0.186/elfutils-0.186.tar.bz2 \
        && tar xjf elfutils-0.186.tar.bz2 \
        && cd elfutils-0.186 \
        && ./configure --prefix=/usr/local --disable-debuginfod \
        && make -j30 \
        && checkinstall --pkgversion="1.0.0" --pkgname=elfutil \
        && ldconfig

# Install dyninst (and generate .deb package)
RUN git clone --depth=1 https://github.com/dyninst/dyninst \
        && cd dyninst \
        && mkdir build && cd build \
        && cmake -DCMAKE_PREFIX_PATH=/usr/local .. \
        && make -j30 \
        && checkinstall --pkgversion="1.0.0" --pkgname=dyninst

# Download + build latest release of AFL++.
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev
RUN git clone https://github.com/AFLplusplus/AFLplusplus /afl && \
    cd /afl && \
    git checkout tags/v4.32c
# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make

# Install dyninst (and generate .deb package)
RUN git clone --depth=1 https://github.com/vanhauser-thc/afl-dyninst \
        && cd afl-dyninst \
        && ln -s ../afl afl \
        && make -j30 \
        && checkinstall --pkgversion="1.0.0" --pkgname=afl-dyninst

# Gather afl-dyninst libs to copy to builder image
RUN mkdir -p /out/afl-dyninst/lib && \
    # find and copy afl-dyninst's shared libraries
    ldd "$(which afl-dyninst)" \
      | awk '/=>/ {print $(NF-1)}' \
      | xargs -I{} cp {} /out/afl-dyninst/lib/ && \
    # copy the runtime library
    cp /usr/local/lib/libdyninstAPI_RT.so /out/afl-dyninst/lib/

# We user PeAR's driver, so download and build that
RUN git clone -b fuzzbench https://github.com/avncharlie/PeAR.git /PeAR
RUN cd /PeAR/utils/pear_driver && make

# Copy all generated packages to install on builder image (should only need afl-dyninst one though)
RUN mkdir -p /debs && \
    find / -type f -name '*.deb' -print0 | \
    xargs -0 cp -t /debs

# Now copy it all over to fuzzbench builder image
FROM $parent_image

# Pull in AFL++ and PeAR driver
COPY --from=afl-dyninst /afl /afl
COPY --from=afl-dyninst /PeAR /PeAR

# Pull in afl-dyninst package and install
COPY --from=afl-dyninst /debs /debs
RUN cd /debs && dpkg -i afl-dyninst*.deb

# Pull in afl-dyninst needed libs
COPY --from=afl-dyninst /out/afl-dyninst /afl-dyninst
RUN set -eux && \
    cp -n /afl-dyninst/lib/* /usr/local/lib/ 
RUN ldconfig
ENV DYNINSTAPI_RT_LIB=/usr/local/lib/libdyninstAPI_RT.so

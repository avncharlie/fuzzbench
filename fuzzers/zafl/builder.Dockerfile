ARG parent_image
FROM $parent_image

# Install the necessary packages.
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        python3.9

# Download latest release of AFL++.
RUN git clone https://github.com/AFLplusplus/AFLplusplus /afl && \
    cd /afl && \
    git checkout tags/v4.32c 
# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make

# We user PeAR's driver, so download and build that
RUN git clone https://github.com/avncharlie/PeAR.git /PeAR
RUN cd /PeAR/utils/pear_driver && make

# ZAFL
RUN apt-get update -y && env DEBIAN_FRONTEND=noninteractive apt install --no-install-recommends -y scons bison flex g++ nasm sharutils gcc-multilib g++-multilib autoconf libelf-dev coreutils makeself postgresql-client libpqxx-dev cmake git unzip wget build-essential python3-dev automake git flex bison libglib2.0-dev libpixman-1-dev python3-setuptools ninja-build tzdata openssl sudo fakeroot file postgresql
RUN env DEBIAN_FRONTEND=noninteractive apt-get install -y lld-12 llvm-12 llvm-12-dev clang-12
RUN env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --reinstall ca-certificates

# cache bust
# ADD https://git.zephyr-software.com/api/v4/projects/27/repository/branches/master /tmp/zipr.killcache
# ADD https://git.zephyr-software.com/api/v4/projects/117/repository/branches/master /tmp/zafl.killcache

ENV USER=root
# checkout and build zipr/zafl, and setup postgres
RUN cd / && \
    git config --global http.sslVerify false && \
    git clone --recursive --depth 1 https://git.zephyr-software.com/opensrc/zipr.git &&\
    git clone --recursive --depth 1 https://git.zephyr-software.com/opensrc/zafl.git

RUN bash -c 'unset CC ; unset CXX; unset CFLAGS; unset CXXFLAGS; cd /zipr ;  \
    service postgresql start ; \
    while ! pg_isready ; do sleep 1 ; done  ; \
    . set_env_vars ;  \
    scons -j3 ; \
    ./postgres_setup.sh  ; \
    cd /zafl ;  \
    . set_env_vars ;  \
    scons -j3 ; \
    cd / ; \
    rm -rf /zipr/irdb-libs /zipr/SMPStaticAnalyzer /*/.git' ; \
    cp /zafl/libzafl/lib/*so /out

ENV LD_LIBRARY_PATH=/zafl/libzafl/lib/

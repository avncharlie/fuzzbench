ARG parent_image

# Build StochFuzz in own container
FROM ubuntu:20.04 as stochfuzz
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get -y install git libtool build-essential wget unzip cmake meson \
    pkg-config clang python3 python3-setuptools xxd
RUN git clone https://github.com/ZhangZhuoSJTU/StochFuzz.git
RUN cd StochFuzz && ./build.sh
RUN cd StochFuzz/src && make release

FROM $parent_image

# Copy build over
COPY --from=stochfuzz /StochFuzz /StochFuzz

# Build last version of AFL++ StochFuzz works with. See https://github.com/ZhangZhuoSJTU/StochFuzz/issues/6
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        clang \
        wget
RUN git clone https://github.com/AFLplusplus/AFLplusplus /afl && \
    cd /afl && \
    git checkout tags/3.10c
# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make

# We user PeAR's driver, so download and build that
RUN git clone -b fuzzbench https://github.com/avncharlie/PeAR.git /PeAR
RUN cd /PeAR/utils/pear_driver && make


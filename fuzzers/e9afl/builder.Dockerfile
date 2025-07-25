ARG parent_image
FROM $parent_image

# Build E9AFL on clean ubuntu 20.04 (doesn't build on parent image)
FROM ubuntu:20.04 AS e9afl
ARG DEBIAN_FRONTEND=noninteractive

# Download + build latest release of AFL++.
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
    git checkout tags/v4.32c
# RUN sed -i 's/^#define DEFAULT_SHMEM_SIZE .*/#define DEFAULT_SHMEM_SIZE 65536/' /afl/include/config.h
# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make

# We user PeAR's driver, so download and build that
RUN git clone -b fuzzbench https://github.com/avncharlie/PeAR.git /PeAR
RUN cd /PeAR/utils/pear_driver && make

# Download and build e9afl
RUN apt-get install -y xxd clang unzip
RUN git clone https://github.com/GJDuck/e9afl.git /e9afl
RUN cd /e9afl && ./build.sh

# Now copy it all over to fuzzbench builder image
FROM $parent_image

# Pull in AFL++ and PeAR driver
COPY --from=e9afl /afl /afl
COPY --from=e9afl /PeAR /PeAR

# Pull in E9AFL
COPY --from=e9afl /e9afl /e9afl

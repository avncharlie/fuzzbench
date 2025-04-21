# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG parent_image
FROM $parent_image

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get -y install --no-install-suggests --no-install-recommends \
    automake \
    cmake \
    meson \
    ninja-build \
    bison flex \
    build-essential \
    git \
    python3 python3-dev python3-setuptools python-is-python3 \
    libtool libtool-bin \
    libglib2.0-dev \
    wget vim jupp nano bash-completion less \
    apt-utils apt-transport-https ca-certificates gnupg dialog \
    libpixman-1-dev \
    gnuplot-nox \
    && rm -rf /var/lib/apt/lists/*

RUN echo "deb http://apt.llvm.org/focal/ llvm-toolchain-focal-13 main" >> /etc/apt/sources.list && \
    wget -qO - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -

RUN echo "deb http://ppa.launchpad.net/ubuntu-toolchain-r/test/ubuntu focal main" >> /etc/apt/sources.list && \
    apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 1E9377A2BA9EF27F

RUN apt-get update && apt-get full-upgrade -y && \
    apt-get -y install --no-install-suggests --no-install-recommends \
    clang-13 clang-tools-13 libc++1-13 libc++-13-dev \
    libc++abi1-13 libc++abi-13-dev libclang1-13 libclang-13-dev \
    libclang-common-13-dev libclang-cpp13 libclang-cpp13-dev liblld-13 \
    liblld-13-dev liblldb-13 liblldb-13-dev libllvm13 libomp-13-dev \
    libomp5-13 lld-13 lldb-13 llvm-13 llvm-13-dev llvm-13-runtime llvm-13-tools

ENV LLVM_CONFIG=llvm-config-13

RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-13 0 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-13 0

# Download afl++.
RUN git clone https://github.com/AFLplusplus/AFLplusplus /afl && \
    cd /afl && \
    git checkout tags/v4.31c 

# Build without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS CXXFLAGS && \
    export CC=clang AFL_NO_X86=1 && \
    PYTHON_INCLUDE=/ make 

# We user PeAR's driver, so download and build that
RUN git clone -b fuzzbench https://github.com/avncharlie/PeAR.git /PeAR
RUN cd /PeAR/ && git fetch && git reset --hard origin/fuzzbench
RUN cd /PeAR/utils/pear_driver && make



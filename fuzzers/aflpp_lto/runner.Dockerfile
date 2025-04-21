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

FROM gcr.io/fuzzbench/base-image


RUN apt-get update && \
    apt-get -y install --no-install-suggests --no-install-recommends \
    git \
    wget \
    apt-utils apt-transport-https ca-certificates gnupg dialog

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

# This makes interactive docker runs painless:
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/out"
ENV PATH="$PATH:/out"

ENV AFL_MAP_SIZE=65536
ENV AFL_SKIP_CPUFREQ=1
ENV AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
ENV AFL_TESTCACHE_SIZE=2

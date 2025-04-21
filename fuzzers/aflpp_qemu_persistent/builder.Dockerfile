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

# Install the necessary packages.
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        flex \
        bison \
        libglib2.0-dev \
        libpixman-1-dev \
        ninja-build \
        libstdc++-$(gcc --version|head -n1|sed 's/\..*//'|sed 's/.* //')-dev


# Download latest release of AFL++.
RUN git clone https://github.com/AFLplusplus/AFLplusplus /afl && \
    cd /afl && \
    git checkout tags/v4.31c 

# Build afl++ without Python support as we don't need it.
# Set AFL_NO_X86 to skip flaky tests.
RUN cd /afl && \
    unset CFLAGS && unset CXXFLAGS && \
    AFL_NO_X86=1 CC=clang PYTHON_INCLUDE=/ make && \
    cd qemu_mode && ./build_qemu_support.sh 

# We user PeAR's driver, so download and build that
RUN git clone -b fuzzbench https://github.com/avncharlie/PeAR.git /PeAR
RUN cd /PeAR/ && git fetch && git reset --hard origin/fuzzbench
RUN cd /PeAR/utils/pear_driver && make

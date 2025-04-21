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
#
"""Integration code for AFLplusplus fuzzer."""

import os
import shutil

from fuzzers import utils
from fuzzers.pear import fuzzer as pear_fuzzer

def build(*args):
    """ Build benchmark. """
    build_directory = os.environ['OUT']

    # move fuzzer to build directory
    shutil.copy('/afl/afl-fuzz', build_directory)

    # options for afl llvm compiler
    os.environ['CC'] = '/afl/afl-clang-fast'
    os.environ['CXX'] = '/afl/afl-clang-fast++'

    # Use shmem driver
    os.environ['FUZZER_LIB'] = '/libAFLDriver.a'

    # Disable address sanitizer
    # os.environ['CFLAGS'] = ' '.join(utils.NO_SANITIZER_COMPAT_CFLAGS)
    # cxxflags = [utils.LIBCPLUSPLUS_FLAG] + utils.NO_SANITIZER_COMPAT_CFLAGS
    # os.environ['CXXFLAGS'] = ' '.join(cxxflags)

    # Disable optimisation
    # os.environ["AFL_DONT_OPTIMIZE"] = '1'

    # Set map size to 64k
    # os.environ['AFL_MAP_SIZE'] = '65536'

    utils.build_benchmark()

def fuzz(input_corpus, output_corpus, target_binary):
    """Run fuzzer."""
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

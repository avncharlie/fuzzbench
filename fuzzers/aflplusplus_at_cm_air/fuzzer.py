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
"""Integration code for AFLplusplus fuzzer."""

# This optimized afl++ variant should always be run together with
# "aflplusplus" to show the difference - a default configured afl++ vs.
# a hand-crafted optimized one. afl++ is configured not to enable the good
# stuff by default to be as close to vanilla afl as possible.
# But this means that the good stuff is hidden away in this benchmark
# otherwise.

import os
import shutil

from fuzzers.aflplusplus import fuzzer as aflplusplus_fuzzer


def build():  # pylint: disable=too-many-branches,too-many-statements
    """Build benchmark."""
    aflplusplus_fuzzer.build('tracepc', 'cmplog', 'dict2file')
    build_directory = os.environ['OUT']
    shutil.copy('/afl/autotokens.so', build_directory)


def fuzz(input_corpus, output_corpus, target_binary):
    """Run fuzzer."""
    run_options = ['-l', '2']

    os.environ['AFL_CMPLOG_ONLY_NEW'] = '1'
    os.environ['AFL_CUSTOM_MUTATOR_LIBRARY'] = './autotokens.so'
    os.environ['AUTOTOKENS_ONLY_FAV'] = '1'
    os.environ['AUTOTOKENS_CREATE_FROM_THIN_AIR'] = '1'

    aflplusplus_fuzzer.fuzz(input_corpus,
                            output_corpus,
                            target_binary,
                            flags=(run_options),
                            skip=True)

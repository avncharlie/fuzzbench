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
""" Integration code for AFLplusplus QEMU mode fuzzer """

import os
import shutil
import subprocess

from fuzzers.pear import fuzzer as pear_fuzzer

def build():
    """Build benchmark."""
    build_directory = os.environ['OUT']

    # move fuzzer and qemu tracer to build directory
    shutil.copy('/afl/afl-fuzz', build_directory)
    shutil.copy('/afl/afl-qemu-trace', build_directory)

    # move hook to build dir
    shutil.copy('/aflpp_driver/aflpp_qemu_driver_hook.so', build_directory)

    pear_fuzzer.build_no_instrumentation('/PeAR/utils/pear_driver/libPeARShmemDriver.a')

def get_symbol_addr(binary, symbol):
    nm_proc = subprocess.run([
        'sh', '-c',
        'nm \'' + binary + f'\' | grep -i \'T {symbol}\''
    ], stdout=subprocess.PIPE, check=True)
    addr = '0x' + nm_proc.stdout.split()[0].decode('utf-8')
    return addr

def fuzz(input_corpus, output_corpus, target_binary):
    """Run fuzzer."""

    target_func = get_symbol_addr(target_binary, 'LLVMFuzzerTestOneInput')

    os.environ['AFL_QEMU_PERSISTENT_ADDR'] = target_func
    os.environ['AFL_ENTRYPOINT'] = target_func
    os.environ['AFL_QEMU_PERSISTENT_CNT'] = '2147483647'
    os.environ['AFL_QEMU_PERSISTENT_HOOK'] = '/out/aflpp_qemu_driver_hook.so'
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary, qemu=True)

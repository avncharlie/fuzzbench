''' Integration for pear (experiments) '''

import os
import shutil

from pathlib import Path

from fuzzers import utils
from fuzzers.pear import fuzzer as pear_fuzzer

def build():
    ''' Build benchmark. '''
    build_dir = os.environ['OUT']

    # Move fuzzer to build directory
    shutil.copy('/afl/afl-fuzz', build_dir)

    # Build target (no sanitizers)
    pear_fuzzer.build_no_instrumentation('/PeAR/utils/pear_driver/libPeARShmemDriver.a')
    target_binary = pear_fuzzer.get_target_binary(build_dir)

    # Run PeAR, with persistent mode on the target func
    pear_fuzzer.create_pear_dirs()
    target_func = 'LLVMFuzzerTestOneInput'
    shmem_hook = '/PeAR/utils/pear_driver/hook.o'
    cmd = f"python3.9 -m pear --ir-cache {pear_fuzzer.IR_CACHE} --input-binary {target_binary} --output-dir {pear_fuzzer.PEAR_OUT} --gen-binary AFL++ --deferred-fuzz-function {target_func} --persistent-mode-function {target_func} --persistent-mode-count 2147483647 --sharedmem-call-function {target_func} --sharedmem-obj {shmem_hook}"
    pear_fuzzer.run_pear(cmd, target_binary)
    #pear_fuzzer.delete_pear_dirs()

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

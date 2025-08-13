''' Integration for pear (persistent mode) '''

import os
import shutil

from pathlib import Path

from fuzzers import utils
from fuzzers.pear import fuzzer as pear_fuzzer

def build():
    ''' Build benchmark. '''
    build_dir = os.environ['OUT']
    pear_fuzzer.create_pear_dirs()

    # Move fuzzer to build directory
    shutil.copy('/afl/afl-fuzz', build_dir)

    # Build target (no sanitizers)
    pear_fuzzer.build_no_instrumentation('/PeAR/utils/pear_driver/libPeARStdinDriver.a')
    target_binary = pear_fuzzer.get_target_binary(build_dir)

    # Handle benchmarks that need hints
    current_benchmark = os.environ.get('benchmark') or os.environ.get('BENCHMARK')
    hint_file = pear_fuzzer.gen_hints_for_special_cases(current_benchmark, target_binary)
    hint_arg = ''
    if hint_file:
        hint_arg = f'--hints {hint_file}'

    # Run PeAR, with persistent mode on the target func
    target_func = 'pear_driver_stdin_input'
    cmd = f"python3.9 -m pear --ir-cache {pear_fuzzer.IR_CACHE} --input-binary {target_binary} --output-dir {pear_fuzzer.PEAR_OUT} {hint_arg} --gen-binary --ignore-nonempty AFL++ --deferred-fuzz-function {target_func} --persistent-mode-function {target_func} --persistent-mode-count 2147483647"
    pear_fuzzer.run_pear(cmd, target_binary)

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

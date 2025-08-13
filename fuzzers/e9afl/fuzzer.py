''' Integration for e9afl '''

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
    pear_fuzzer.build_no_instrumentation('/PeAR/utils/pear_driver/libPeARStdinDriver.a')
    target_binary = pear_fuzzer.get_target_binary(build_dir)

    # Run E9AFL
    inst_path = f"/src/{os.path.basename(target_binary)}.afl" # where E9AFL will put generated binary
    cmd = f"/e9afl/e9afl {target_binary}"
    print('Running: ' + cmd)
    os.system(cmd)
    if not os.path.isfile(inst_path):
        print('e9afl-instrumentation failed!')
    else:
        shutil.copy(inst_path, target_binary)

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

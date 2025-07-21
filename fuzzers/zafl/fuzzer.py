''' Integration for zafl (experiments) '''

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

    # Run ZAFL
    inst_path = f"{target_binary}.zafl"
    setup_cmd = "service postgresql start && cd /zipr && . ./set_env_vars && cd /zafl && . ./set_env_vars"
    zafl_cmd = f"zafl.sh {target_binary} {inst_path}"
    bash_cmd = '/bin/bash -c "' + setup_cmd + " && " + zafl_cmd + '"'
    print('Running: ' + bash_cmd)
    os.system(bash_cmd)
    shutil.copy(inst_path, target_binary)

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

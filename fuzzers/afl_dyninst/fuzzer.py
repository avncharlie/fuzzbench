''' Integration for afl-dyninst '''

import os
import shutil

from pathlib import Path

from fuzzers import utils
from fuzzers.pear import fuzzer as pear_fuzzer

def build():
    ''' Build benchmark. '''
    build_dir = os.environ['OUT']

    # Move fuzzer + afl-dyninst runtime libraries to build directory
    shutil.copy('/afl/afl-fuzz', build_dir)
    shutil.copy('/usr/local/lib/libdyninstAPI_RT.so', build_dir)
    shutil.copy('/usr/local/lib/libAflDyninst.so', build_dir)

    # Build target (no sanitizers)
    pear_fuzzer.build_no_instrumentation('/PeAR/utils/pear_driver/libPeARStdinDriver.a')
    target_binary = pear_fuzzer.get_target_binary(build_dir)

    # Run afl-dyninst
    inst_path = f"{target_binary}.afl-dyninst"
    cmd = f"afl-dyninst -i {target_binary} -o {inst_path} -x"
    print('Running: ' + cmd)
    os.system(cmd)
    shutil.copy(inst_path, target_binary)

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    # Copy runtime libraries to library path 
    shutil.copy('/out/libdyninstAPI_RT.so', '/usr/local/lib/')
    shutil.copy('/out/libAflDyninst.so', '/usr/local/lib/')
    os.system('ldconfig')
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

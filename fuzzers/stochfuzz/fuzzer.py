''' Integration for e9afl (experiments) '''

import os
import time
import shutil
import subprocess

from pathlib import Path

from fuzzers import utils
from fuzzers.pear import fuzzer as pear_fuzzer

# Allow stochfuzz 20min to rewrite
TIMEOUT = 60*20

def build():
    ''' Build benchmark. '''
    build_dir = os.environ['OUT']

    # Move fuzzer to build directory
    shutil.copy('/afl/afl-fuzz', build_dir)
    shutil.copytree('/StochFuzz/', os.path.join(build_dir, 'StochFuzz'),
                    dirs_exist_ok=True)

    # Build target (no sanitizers)
    pear_fuzzer.build_no_instrumentation('/PeAR/utils/pear_driver/libPeARStdinDriver.a')
    # Stochfuzz will rewrite binary 'live' as it fuzzes it, so we rewrite in 
    #   runner stage, not now

def wait_for_stochfuzz(phantom_path, timeout=None):
    start_time = time.time()
    while True:
        if os.path.exists(phantom_path):
            print(f"[✓] Phantom file created: {phantom_path}")
            return True
        if timeout is not None and time.time() - start_time > timeout:
            print("[!] Timeout waiting for phantom file.")
            return False
        time.sleep(0.1)

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''

    # 1. Run stochfuzz process 
    # only log fatal errors (to not blow up log file)
    cmd = ['/out/StochFuzz/src/stoch-fuzz',
           '-l', 'FATAL',
           # '-e', '-f', '-i',
           '-r', # enable advanced usage
           '--', target_binary]
    print(f"Running: {' '.join(cmd)}")
    # redirect output to file
    log = "/out/stochfuzz.log"
    with open(log, "w") as log_file:
        p = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT)
    phantom = f'{target_binary}.phantom'

    # 2. Wait for StochFuzz to generate phantom binary
    if not wait_for_stochfuzz(phantom, TIMEOUT):
        exit(1)

    # 3. Fuzz with custom preload
    stochfuzz_preload = subprocess.check_output(
        ['/out/StochFuzz/scripts/stochfuzz_env.sh'],
        text=True
    ).strip()
    os.environ['AFL_PRELOAD'] = stochfuzz_preload
    pear_fuzzer.run_aflpp_fuzz(input_corpus, output_corpus, phantom)

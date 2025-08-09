''' Integration for pear (experiments) '''

import os
import json
import shutil
import subprocess

from pathlib import Path

from fuzzers import utils

DEBUG = True
IR_CACHE = '/ir_cache'
PEAR_OUT = '/pear_out'

def create_pear_dirs():
    os.mkdir(IR_CACHE)
    os.mkdir(PEAR_OUT)

def delete_pear_dirs():
    shutil.rmtree(IR_CACHE)
    shutil.rmtree(PEAR_OUT)

def build_no_instrumentation(fuzzer_lib):
    # Standard basic build for benchmark
    unsafe_prod = '-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION' # needed for libjpeg to compile

    os.environ['CC'] = 'clang'
    os.environ['CXX'] = 'clang++'
    cflags = utils.NO_SANITIZER_COMPAT_CFLAGS + [unsafe_prod] + ['-O3']
    os.environ['CFLAGS'] = ' '.join(cflags)
    cxxflags = [utils.LIBCPLUSPLUS_FLAG] + [unsafe_prod] + utils.NO_SANITIZER_COMPAT_CFLAGS + ['-O3']
    os.environ['CXXFLAGS'] = ' '.join(cxxflags)
    os.environ['FUZZER_LIB'] = fuzzer_lib
    utils.build_benchmark()

def get_target_binary(build_dir):
    # Get target binary path
    target_name = os.getenv('FUZZ_TARGET')
    target_binary = Path(build_dir) / target_name
    assert target_binary.is_file(), 'Cannot find target binary!'
    return target_binary

def run_pear(cmd, target_binary):
    # Run PeAR
    os.chdir('/PeAR')
    print(f'Rewriting with cmd: {cmd}')
    r = os.system(cmd)
    assert r == 0, 'Rewrite failed!'

    # Overwrite original binary with instrumented one
    rewritten = Path(PEAR_OUT) / f'{target_binary.name}.AFL++.exe'
    shutil.copy(rewritten, target_binary)
    print(f'Copied instrumented binary to {target_binary}.')

def gen_hints_for_special_cases(benchmark, target_binary):
    # Add hints to help edge cases
    hints_out = Path(PEAR_OUT) / 'hints.csv'
    base_ir = Path(PEAR_OUT) / 'base.gtirb'

    if benchmark not in ['libjpeg-turbo_libjpeg_turbo_fuzzer',
                         'curl_curl_fuzzer_http']:
        return

    # First, run ddisasm on base binary
    cmd = ['ddisasm', str(target_binary), '--ir', str(base_ir)]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Cmd to generate hints
    cmd = [
        'python3.9', '/PeAR/pear/tools/gen_hints.py',
        '--ir', str(base_ir),
        '--out', str(hints_out)
    ]
    if benchmark == 'curl_curl_fuzzer_http':
        # Curl has data tables that ddisasm incorrectly finds instructions in.
        cmd += ['--data-symbols', json.dumps({
            'K256': 256, 'K256_shaext': 256, 'K_XX_XX': 176
        })]
        cmd += ['--data-between-funcs', json.dumps({
            'AES_cbc_encrypt': '_vpaes_encrypt_core',
            'Camellia_Ekeygen': 'Camellia_cbc_encrypt'
        })]
    elif benchmark == 'libjpeg-turbo_libjpeg_turbo_fuzzer':
        # Libjpeg contains a constant that ddisasm incorrectly disassembles as
        # a symbolic operand (it looks like an address)
        find_fault_ins = f"objdump -M intel -d {target_binary} 2>/dev/null " + r"""| grep -A 500 build_rgb_y_table.*: | awk '/cmp/ {print "0x"$1; exit}'"""
        print(f"Running: {find_fault_ins}")
        faulty_addr = subprocess.check_output(find_fault_ins, shell=True, text=True).strip()[:-1]
        print(f"Found faulty address: {faulty_addr}")
        cmd += ['--not-symbolic-operands', json.dumps({faulty_addr: 1})]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    return hints_out

def build():
    ''' Build benchmark. '''
    build_dir = os.environ['OUT']
    create_pear_dirs()

    # Move fuzzer to build directory
    shutil.copy('/afl/afl-fuzz', build_dir)

    # Build target (no sanitizers)
    build_no_instrumentation('/PeAR/utils/pear_driver/libPeARStdinDriver.a')
    target_binary = get_target_binary(build_dir)
    if DEBUG:
        os.system(f"cp -r {target_binary} {target_binary}.orig")

    # Handle benchmarks that need hints
    current_benchmark = os.environ.get('benchmark') or os.environ.get('BENCHMARK')
    hint_file = gen_hints_for_special_cases(current_benchmark, target_binary)
    hint_arg = ''
    if hint_file:
        hint_arg = f'--hints {hint_file}'

    # Run PeAR
    target_func = 'pear_driver_stdin_input'
    cmd = f"python3.9 -m pear --ir-cache {IR_CACHE} --input-binary {target_binary} --output-dir {PEAR_OUT} {hint_arg} --gen-binary --ignore-nonempty AFL++ --deferred-fuzz-function {target_func}"
    run_pear(cmd, target_binary)
    if DEBUG:
        os.system('cp -r /pear_out /out/')
        os.system('cp -r /ir_cache /out/')

# Code copied from afl/fuzzer.py and aflplusplus/fuzzer.py
def prepare_aflpp_fuzz_environment(input_corpus):
    # Tell AFL to not use its terminal UI so we get usable logs.
    # os.environ['AFL_NO_UI'] = '1'
    # Skip AFL's CPU frequency check (fails on Docker).
    os.environ['AFL_SKIP_CPUFREQ'] = '1'
    # No need to bind affinity to one core, Docker enforces 1 core usage.
    os.environ['AFL_NO_AFFINITY'] = '1'
    # AFL will abort on startup if the core pattern sends notifications to
    # external programs. We don't care about this.
    os.environ['AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES'] = '1'
    # Don't exit when crashes are found. This can happen when corpus from
    # OSS-Fuzz is used.
    os.environ['AFL_SKIP_CRASHES'] = '1'
    # Shuffle the queue (randomisation between trials?)
    os.environ['AFL_SHUFFLE_QUEUE'] = '1'
    # Fast calibration
    os.environ['AFL_FAST_CAL'] = '1'
    # Ignore instability warnings
    os.environ['AFL_NO_WARN_INSTABILITY'] = '1'
    # AFL needs at least one non-empty seed to start.
    utils.create_seed_file_for_empty_corpus(input_corpus)

# Code copied from afl/fuzzer.py and aflplusplus/fuzzer.py
def run_aflpp_fuzz(input_corpus, output_corpus, target_binary, file_input=False, qemu=False):
    prepare_aflpp_fuzz_environment(input_corpus)

    command = [ './afl-fuzz' ]
    if qemu:
        command.append('-Q')
    command += [
        '-i', input_corpus,
        '-o', output_corpus,
        '-m', 'none',   # No memory limit
        '-t', '1000+',  # Use default 1 sec timeout, but add '+' to skip hangs.
    ]
    # Add dictionary if it exists
    dictionary_path = utils.get_dictionary_path(target_binary)
    if dictionary_path:
        command += ['-x', dictionary_path]
    command += ['--', target_binary]
    if file_input:
        command.append('@@')

    print('Running command: ' + ' '.join(command))
    subprocess.check_call(command)

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    run_aflpp_fuzz(input_corpus, output_corpus, target_binary)

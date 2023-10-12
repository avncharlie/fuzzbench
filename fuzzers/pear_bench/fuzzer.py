''' Integration for pear (experiments) '''

import os
import json
import shutil
import subprocess
from collections import namedtuple

from fuzzers import utils
from fuzzers.aflplusplus import fuzzer as aflplusplus_fuzzer

def fixup_riz_register(asm_path):
    '''
    Fixes rewriter output from curl and openssl benchmarks

    Replaces an instruction that references the %riz register with an
    equivalent instruction that doesn't use it.

    Apparently the first instruction is valid, but cannot be assembled with
    GNU assembler (it will complain about %riz not being a valid register).

    %riz / %eiz is apparently a 'psuedo-register' that always evaluates to zero.
    It is used for code alignment reasons (to generate longer instructions) so
    maybe this replacement will cause issues elsewhere.. unsure
    '''
    fixed_asm = None
    with open(asm_path) as f:
        fixed_asm = f.read().replace('andb %bh,(%rcx,%riz,2)', 'andb (%rcx), %bh')

    with open(asm_path, 'w') as f:
        f.write(fixed_asm)

def get_stats(output_corpus, fuzzer_log):  # pylint: disable=unused-argument
    """Gets fuzzer stats for AFL."""
    # Get a dictionary containing the stats AFL reports.
    stats_file = os.path.join(output_corpus, 'fuzzer_stats')
    if not os.path.exists(stats_file):
        print('Can\'t find fuzzer_stats')
        return '{}'
    with open(stats_file, encoding='utf-8') as file_handle:
        stats_file_lines = file_handle.read().splitlines()
    stats_file_dict = {}
    for stats_line in stats_file_lines:
        key, value = stats_line.split(': ')
        stats_file_dict[key.strip()] = value.strip()

    # Report to FuzzBench the stats it accepts.
    stats = {'execs_per_sec': float(stats_file_dict['execs_per_sec'])}
    return json.dumps(stats)

def build():
    ''' Build benchmark. '''
    build_directory = os.environ['OUT']

    # move fuzzer to build directory
    shutil.copy('/afl/afl-fuzz', build_directory)

    # build benchmark
    os.environ['CC'] = 'clang'
    os.environ['CXX'] = 'clang++'
    os.environ['CFLAGS'] = ' '.join(utils.NO_SANITIZER_COMPAT_CFLAGS)
    cxxflags = [utils.LIBCPLUSPLUS_FLAG] + utils.NO_SANITIZER_COMPAT_CFLAGS
    os.environ['CXXFLAGS'] = ' '.join(cxxflags)
    os.environ['FUZZER_LIB'] = '/afl-rewrite/util/libAFLRewriteDriver.a'
    utils.build_benchmark()

    # rewrite target
    target_binary_name = os.getenv('FUZZ_TARGET')
    target_binary_path = os.path.join(os.environ['OUT'], target_binary_name)
    if not os.path.isfile(target_binary_path):
        print('cannot find target binary :(')
        exit(1)
    print(f'Target binary: {target_binary_path}')
    print('Rewriting ...')

    # generate rewritten IR 
    os.environ['TARGET'] = target_binary_path
    os.system('make -C /afl-rewrite fuzzbench')

    # handle edge cases / bugs in gtirb-pprinter to make some benchmarks work
    try:
        current_benchmark = os.environ['benchmark']
    except KeyError:
        current_benchmark = os.environ['BENCHMARK']
    # edge case handlers will modify and build rewritten asm needed 
    EdgeCaseHandler = namedtuple("EdgeCaseHandler", ["handler_func", "build_cmd"])
    edge_cases = {
        'curl_curl_fuzzer_http': EdgeCaseHandler(
            fixup_riz_register, 
            'gcc -o {output_binary} {fixed_asm} -ldl -lm -lpthread -lgcc_s -lc -no-pie -nostartfiles'
        ),
        'openssl_x509': EdgeCaseHandler(
            fixup_riz_register, 
            'gcc -o {output_binary} {fixed_asm} -ldl -lm -lpthread -lgcc_s -no-pie -nostartfiles'
        ),
        'systemd_fuzz-link-parser': EdgeCaseHandler(
            # gtirb-pprinter doesn't generate compilation command correctly for
            # this benchmark, so we do it ourselves.
            lambda x: None, 
            'gcc -o {output_binary} {fixed_asm} -l:libdl.so.2 -l:libm.so.6 -l:libsystemd-shared-251.so -l:libgcc_s.so.1 -l:libpthread.so.0 -l:libc.so.6 -L/out/src/shared -Wl,-rpath,/out/src/shared -no-pie -nostartfiles -no-pie -nostartfiles'
        )
    }

    if current_benchmark in edge_cases:
        # rewrite and generate asm
        asm_path = f'{target_binary_path}.S'
        os.system(f'gtirb-pprinter /afl-rewrite/out/{target_binary_name}-afl.gtirb --asm {asm_path}')

        # fix generated asm as needed
        edge_cases[current_benchmark].handler_func(asm_path)

        # build benchmark as specified
        build_cmd = edge_cases[current_benchmark].build_cmd.format(
            output_binary=target_binary_path,
            fixed_asm=asm_path
        )
        print(f'Building {current_benchmark} with command: {build_cmd}')
        os.system(build_cmd)
    else:
        # generate binary (gtirb-pprinter generates assembly and will
        # automatically create a command to assemble generated asm)
        os.system(f'gtirb-pprinter /afl-rewrite/out/{target_binary_name}-afl.gtirb --binary {target_binary_path}')

def fuzz(input_corpus, output_corpus, target_binary):
    ''' run benchmark. '''
    aflplusplus_fuzzer.fuzz(input_corpus, output_corpus, target_binary)
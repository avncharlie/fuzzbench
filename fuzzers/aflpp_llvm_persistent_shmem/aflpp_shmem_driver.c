//
// aflpp shared memory driver
//

#ifdef __cplusplus
extern "C" {

#endif

#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <limits.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>
#ifndef __HAIKU__
  #include <sys/syscall.h>
#endif

#include "config.h"
#include "types.h"
#include "cmplog.h"

#ifdef _DEBUG
  #include "hash.h"
#endif

// AFL++ shared memory fuzz cases
int                   __afl_sharedmem_fuzzing = 1;
extern unsigned int  *__afl_fuzz_len;
extern unsigned char *__afl_fuzz_ptr;

// AFL++ coverage map
extern unsigned char *__afl_area_ptr;
extern unsigned int   __afl_map_size;

// libFuzzer interface is thin, so we don't include any libFuzzer headers.
/* Using the weak attributed on LLVMFuzzerTestOneInput() breaks oss-fuzz but
   on the other hand this is what Google needs to make LLVMFuzzerRunDriver()
   work. Choose your poison Google! */
/*__attribute__((weak))*/ int LLVMFuzzerTestOneInput(const uint8_t *Data,
                                                     size_t         Size);
__attribute__((weak)) int     LLVMFuzzerInitialize(int *argc, char ***argv);
__attribute__((weak)) void    LLVMFuzzerCleanup(void);
__attribute__((weak)) int     LLVMFuzzerRunDriver(
        int *argc, char ***argv, int (*callback)(const uint8_t *data, size_t size));

// Default nop ASan hooks for manual poisoning when not linking the ASan
// runtime
// https://github.com/google/sanitizers/wiki/AddressSanitizerManualPoisoning
__attribute__((weak)) void __asan_poison_memory_region(
    void const volatile *addr, size_t size) {

  (void)addr;
  (void)size;

}

__attribute__((weak)) void __asan_unpoison_memory_region(
    void const volatile *addr, size_t size) {

  (void)addr;
  (void)size;

}

__attribute__((weak)) void *__asan_region_is_poisoned(void *beg, size_t size);

// Notify AFL about persistent mode.
__attribute__((section(".rodata"), used,
               retain)) static const char AFL_PERSISTENT[] =
    "##SIG_AFL_PERSISTENT##";
int __afl_persistent_loop(unsigned int);

// Notify AFL about deferred forkserver.
__attribute__((section(".rodata"), used,
               retain)) static const char AFL_DEFER_FORKSVR[] =
    "##SIG_AFL_DEFER_FORKSRV##";
void __afl_manual_init();

__attribute__((weak)) int main(int argc, char **argv) {
  return LLVMFuzzerRunDriver(&argc, &argv, LLVMFuzzerTestOneInput);
}

// Execute any files provided as parameters.
static int ExecuteFilesOnyByOne(int argc, char **argv,
                                int (*callback)(const uint8_t *data,
                                                size_t         size)) {
  unsigned char *buf = (unsigned char *)malloc(MAX_FILE);
  ssize_t prev_length = 0;
  for (int i = 1; i < argc; i++) {
    int fd = 0;
    if (strcmp(argv[i], "-") != 0) { fd = open(argv[i], O_RDONLY); }
    if (fd == -1) { continue; }
    ssize_t length = syscall(SYS_read, fd, buf, MAX_FILE);
    if (length > 0) {
      prev_length = length;
      printf("Reading %zu bytes from %s\n", length, argv[i]);
      callback(buf, length);
      printf("Execution successful.\n");
    }
    if (fd > 0) { close(fd); }
  }

  free(buf);
  return 0;
}

#define kMaxAflInputSize (1 * 1024 * 1024)
static uint8_t AflInputBuf[kMaxAflInputSize];

__attribute__((weak)) int LLVMFuzzerRunDriver(
    int *argcp, char ***argvp,
    int (*callback)(const uint8_t *data, size_t size)) {

  int    argc = *argcp;
  char **argv = *argvp;

  // Exec as normal if not in afl
  bool in_afl = !(!getenv(SHM_FUZZ_ENV_VAR) || !getenv(SHM_ENV_VAR) ||
                  fcntl(FORKSRV_FD, F_GETFD) == -1 ||
                  fcntl(FORKSRV_FD + 1, F_GETFD) == -1);
  if (!in_afl && argc == 2 && !strcmp(argv[1], "-")) {
    __afl_manual_init();
    return ExecuteFilesOnyByOne(argc, argv, callback);
  } else if (!in_afl && argc > 1 && argv[1][0] != '-') {
    if (argc == 2) { __afl_manual_init(); }
    return ExecuteFilesOnyByOne(argc, argv, callback);
  } 

  // Otherwise fuzz
  if (LLVMFuzzerInitialize) {
    fprintf(stderr, "Running LLVMFuzzerInitialize ...\n");
    LLVMFuzzerInitialize(&argc, &argv);
    fprintf(stderr, "continue...\n");
  }

  int N = INT_MAX;
  __afl_manual_init();
  while (__afl_persistent_loop(N)) {
    if (unlikely(callback(__afl_fuzz_ptr, *__afl_fuzz_len) == -1)) {
      memset(__afl_area_ptr, 0, __afl_map_size);
      __afl_area_ptr[0] = 1;
    }
  }

  if (LLVMFuzzerCleanup) {
    fprintf(stderr, "Running LLVMFuzzerCleanup ...\n");
    LLVMFuzzerCleanup();
    fprintf(stderr, "Exiting ...\n");
  }
  return 0;

}

#ifdef __cplusplus

}

#endif

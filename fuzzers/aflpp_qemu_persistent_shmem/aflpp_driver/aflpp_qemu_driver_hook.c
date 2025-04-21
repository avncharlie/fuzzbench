#include "api.h"

#include <stdint.h>
#include <string.h>

#define g2h(x) ((void *)((unsigned long)(x) + guest_base))
#define h2g(x) ((uint64_t)(x) - guest_base)

#define kMaxAflInputSize (1 * 1024 * 1024)

void afl_persistent_hook(struct x86_64_regs *regs, uint64_t guest_base,
                         uint8_t *input_buf, uint32_t input_buf_len) {
  if (input_buf_len > kMaxAflInputSize)
    input_buf_len = kMaxAflInputSize;
  memcpy(g2h(regs->rdi), input_buf, input_buf_len);
  regs->rsi = input_buf_len;
}

#undef g2h
#undef h2g

int afl_persistent_hook_init(void) {

  // 1 for shared memory input (faster), 0 for normal input (you have to use
  // read(), input_buf will be NULL)
  return 1;

}


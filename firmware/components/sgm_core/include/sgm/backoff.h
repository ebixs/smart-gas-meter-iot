/*
 * Exponential retry backoff with "equal jitter": the delay for attempt k is
 * d/2 + random(0..d/2) with d = min(cap, base * 2^k). The jitter spreads a
 * fleet's retries after a network outage instead of synchronising them.
 */
#ifndef SGM_BACKOFF_H
#define SGM_BACKOFF_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t base_ms;
    uint32_t cap_ms;
    uint32_t attempt;
    uint32_t rng; /* xorshift32 state, never 0 */
} sgm_backoff_t;

void sgm_backoff_init(sgm_backoff_t *b, uint32_t base_ms, uint32_t cap_ms, uint32_t seed);
uint32_t sgm_backoff_next(sgm_backoff_t *b);
void sgm_backoff_reset(sgm_backoff_t *b);

#ifdef __cplusplus
}
#endif
#endif

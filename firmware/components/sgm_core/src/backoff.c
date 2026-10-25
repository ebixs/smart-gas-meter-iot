#include "sgm/backoff.h"

void sgm_backoff_init(sgm_backoff_t *b, uint32_t base_ms, uint32_t cap_ms, uint32_t seed)
{
    b->base_ms = base_ms ? base_ms : 1;
    b->cap_ms = cap_ms < b->base_ms ? b->base_ms : cap_ms;
    b->attempt = 0;
    b->rng = seed ? seed : 0x9E3779B9u;
}

static uint32_t xorshift32(uint32_t *s)
{
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *s = x;
    return x;
}

uint32_t sgm_backoff_next(sgm_backoff_t *b)
{
    uint64_t d = (uint64_t)b->base_ms << (b->attempt < 32 ? b->attempt : 32);
    if (d > b->cap_ms) {
        d = b->cap_ms;
    }
    if (b->attempt < 32) {
        b->attempt++;
    }
    uint32_t half = (uint32_t)(d / 2);
    return half + xorshift32(&b->rng) % ((uint32_t)d - half + 1);
}

void sgm_backoff_reset(sgm_backoff_t *b) { b->attempt = 0; }

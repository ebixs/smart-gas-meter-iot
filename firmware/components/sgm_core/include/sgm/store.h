/*
 * Power-loss-safe persistence of the cumulative counter.
 *
 * Two slots (A/B) hold a 40-byte little-endian image protected by CRC-32.
 * Each save writes the slot that does NOT hold the newest image, so a reset
 * in the middle of a write can only damage the older copy. Load picks the
 * valid image with the highest generation.
 *
 * Flash wear: one save of a 40-byte NVS blob costs ~4 of the 126 entries in
 * a 4 KiB page, and the 24 KiB NVS partition rotates over 6 pages. Saving on
 * every pulse lasts ~84 years for the simulated fleet's median household
 * (2,250 m3/year at 0.01 m3/pulse) and ~24 years at its 99th percentile.
 * See firmware/README.md for the full budget.
 */
#ifndef SGM_STORE_H
#define SGM_STORE_H

#include <stddef.h>
#include <stdint.h>

#include "sgm/period.h"

#ifdef __cplusplus
extern "C" {
#endif

#define SGM_STORE_IMAGE_LEN 40
#define SGM_STORE_MAGIC 0x53474D31u /* "SGM1" */
#define SGM_STORE_VERSION 1

typedef struct {
    uint32_t generation;
    uint32_t sequence;      /* last telemetry sequence handed out */
    uint64_t pulse_total;   /* cumulative qualified pulses */
    sgm_period_t open_period;
    uint32_t boot_count;
} sgm_persist_t;

typedef struct {
    /* Return 0 on success, non-zero when the slot is empty or unreadable. */
    int (*read)(void *ctx, int slot, uint8_t *buf, size_t len);
    int (*write)(void *ctx, int slot, const uint8_t *buf, size_t len);
    void *ctx;
} sgm_store_io_t;

enum { SGM_STORE_OK = 0, SGM_STORE_EMPTY = 1, SGM_STORE_IO_ERROR = -1 };

uint32_t sgm_crc32(const uint8_t *data, size_t len);
void sgm_store_encode(const sgm_persist_t *st, uint8_t out[SGM_STORE_IMAGE_LEN]);
/* Returns 0 when the image is valid. */
int sgm_store_decode(const uint8_t in[SGM_STORE_IMAGE_LEN], sgm_persist_t *st);

int sgm_store_load(const sgm_store_io_t *io, sgm_persist_t *out);
/* Increments st->generation and writes the older slot. */
int sgm_store_save(const sgm_store_io_t *io, sgm_persist_t *st);

typedef struct {
    uint32_t every_pulses; /* save after this many new pulses (1 = every pulse) */
    uint32_t max_age_ms;   /* or when unsaved pulses are older than this */
} sgm_commit_policy_t;

int sgm_store_should_commit(const sgm_commit_policy_t *p, uint64_t unsaved_pulses, uint64_t ms_since_save);

#ifdef __cplusplus
}
#endif
#endif

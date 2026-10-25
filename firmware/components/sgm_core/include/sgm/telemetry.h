/*
 * JSON encoder for telemetry contract v2 (schemas/telemetry-v2.schema.json).
 * Fixed buffers, no heap, no libc time functions: identical output on the
 * device and in host tests.
 */
#ifndef SGM_TELEMETRY_H
#define SGM_TELEMETRY_H

#include <stddef.h>
#include <stdint.h>

#include "sgm/record.h"

#ifdef __cplusplus
extern "C" {
#endif

#define SGM_TELEMETRY_SCHEMA_VERSION 2

typedef struct {
    const char *device_id;  /* <= 64 chars, [A-Za-z0-9._-] */
    const char *fw_version; /* e.g. "0.3.0+g1a2b3c4" */
    const char *input_mode; /* "bench_pulse" on hardware, "simulated" in host demos */
} sgm_device_info_t;

enum {
    SGM_JSON_NO_SPACE = -1,
    SGM_JSON_UNSYNCED = -2, /* record has no wall-clock time yet */
    SGM_JSON_BAD_DEVICE_ID = -3,
};

/* ISO 8601 UTC with milliseconds: "2026-10-24T08:30:00.000Z" (24 chars + NUL). */
int sgm_format_utc(int64_t unix_ms, char *out, size_t n);

/* Writes one JSON object (no trailing newline). Returns length or SGM_JSON_*. */
int sgm_telemetry_json(const sgm_record_t *rec, const sgm_device_info_t *dev, char *out, size_t n);

/* Writes a JSON array of records [rec0,...]. Stops before the first record that
 * does not fit or is unsynced; *encoded receives how many were written. */
int sgm_telemetry_batch_json(const sgm_record_t *const *recs, size_t count, const sgm_device_info_t *dev,
                             char *out, size_t n, size_t *encoded);

#ifdef __cplusplus
}
#endif
#endif

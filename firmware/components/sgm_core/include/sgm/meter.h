/*
 * Meter core: counting, persistence, wall clock, billing-period self-reading
 * and record creation, independent of ESP-IDF. The device firmware calls it
 * from the pulse task; host tests drive it with simulated time.
 *
 * Ordering rules that keep the backend's monotonic checks valid:
 *   - every record gets the next sequence number, and the sequence is saved
 *     to flash before the record is queued, so a reset never reuses one;
 *   - every path that creates a record first checks for a period boundary,
 *     so a period-close record always precedes later records;
 *   - a record's timestamp is never earlier than the previous record's.
 */
#ifndef SGM_METER_H
#define SGM_METER_H

#include <stdbool.h>
#include <stdint.h>

#include "sgm/period.h"
#include "sgm/queue.h"
#include "sgm/record.h"
#include "sgm/store.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    sgm_persist_t st;
    sgm_store_io_t io;
    sgm_commit_policy_t policy;
    sgm_period_tracker_t periods;
    sgm_queue_t *queue;

    uint64_t unsaved_pulses;
    uint64_t last_save_uptime_ms;

    bool synced;
    uint8_t time_source;
    int64_t sync_unix_ms;
    uint64_t sync_uptime_ms;
    int64_t last_record_unix_ms;

    uint16_t pending_events; /* attached to the next record */
    int16_t rssi_dbm;
    uint16_t supply_mv;
    uint32_t store_errors;
} sgm_meter_t;

typedef struct {
    sgm_store_io_t io;
    sgm_commit_policy_t policy;
    sgm_queue_t *queue;
    int period_months;     /* 1 monthly, 3 seasonal */
    int32_t tz_offset_s;   /* SGM_TZ_IRAN_S */
    uint16_t boot_events;  /* reset cause, e.g. SGM_EVT_BROWNOUT_RESET */
} sgm_meter_cfg_t;

/* Loads the persisted counter, records the boot and queues a boot event record. */
void sgm_meter_boot(sgm_meter_t *m, const sgm_meter_cfg_t *cfg, uint64_t uptime_ms);

/* Wall clock became known (or was corrected). Backfills queued records. */
void sgm_meter_set_time(sgm_meter_t *m, int64_t unix_ms, uint64_t uptime_ms, uint8_t source);
bool sgm_meter_now(const sgm_meter_t *m, uint64_t uptime_ms, int64_t *unix_ms);

/* One qualified pulse. implausible = the qualifier saw it faster than Qmax. */
void sgm_meter_pulse(sgm_meter_t *m, uint64_t uptime_ms, bool implausible);

/* Periodic housekeeping: period boundary and age-based commit. */
void sgm_meter_tick(sgm_meter_t *m, uint64_t uptime_ms);

/* Queue an interval record with the current counter. */
void sgm_meter_snapshot(sgm_meter_t *m, uint64_t uptime_ms);

/* Queue an event-only record now. */
void sgm_meter_event(sgm_meter_t *m, uint16_t events, uint64_t uptime_ms);

/* Persist now if anything is unsaved (before sleep or a planned restart). */
void sgm_meter_flush(sgm_meter_t *m, uint64_t uptime_ms);

#ifdef __cplusplus
}
#endif
#endif

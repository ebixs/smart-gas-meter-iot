/*
 * Telemetry record held in the device queue until the backend acknowledges it.
 *
 * The record keeps the raw cumulative pulse count. Conversion to volume is a
 * server-side decision that needs a verified, meter-specific pulse constant.
 */
#ifndef SGM_RECORD_H
#define SGM_RECORD_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    SGM_REC_INTERVAL = 0,     /* periodic snapshot of the cumulative counter */
    SGM_REC_PERIOD_CLOSE = 1, /* counter frozen at a billing-period boundary ("self-reading") */
    SGM_REC_EVENT = 2,        /* state change only (tamper, restore, overflow, ...) */
} sgm_rec_type_t;

typedef enum {
    SGM_TIME_UNSYNCED = 0,   /* wall clock unknown: the record cannot be sent yet */
    SGM_TIME_NETWORK = 1,    /* cellular network time (NITZ via AT+CCLK) */
    SGM_TIME_SNTP = 2,       /* SNTP over Wi-Fi (bench builds) */
    SGM_TIME_BACKFILLED = 3, /* created before sync; time derived from uptime after sync */
} sgm_time_source_t;

/* Event flags; bit order defines the order of the JSON "events" array. */
enum {
    SGM_EVT_TAMPER_OPEN = 1u << 0,
    SGM_EVT_TAMPER_CLOSED = 1u << 1,
    SGM_EVT_COUNTER_RESTORED = 1u << 2, /* counter reloaded from flash after a reset */
    SGM_EVT_STORE_EMPTY = 1u << 3,      /* no valid persisted counter: started from zero */
    SGM_EVT_QUEUE_OVERFLOW = 1u << 4,   /* older interval records were dropped */
    SGM_EVT_IMPLAUSIBLE_RATE = 1u << 5, /* pulses faster than the meter's Qmax allows */
    SGM_EVT_LATE_CLOSE = 1u << 6,       /* period closed after the boundary (device was off) */
    SGM_EVT_BROWNOUT_RESET = 1u << 7,
    SGM_EVT_WATCHDOG_RESET = 1u << 8,
};
#define SGM_EVT_COUNT 9

typedef struct {
    uint32_t sequence;
    uint8_t type;        /* sgm_rec_type_t */
    uint8_t time_source; /* sgm_time_source_t */
    uint16_t events;     /* SGM_EVT_* */
    int64_t unix_ms;     /* 0 while unsynced */
    uint64_t uptime_ms;
    uint64_t pulse_total;
    int16_t rssi_dbm;    /* SGM_RSSI_UNKNOWN when not measured */
    uint16_t supply_mv;  /* 0 when not measured */
    int16_t period_year; /* Jalali year of the closed period (period_close only) */
    uint8_t period_month;
    uint8_t period_months; /* 1 = monthly, 3 = seasonal */
    uint8_t flags;         /* SGM_RECF_*, device-internal, never serialized */
} sgm_record_t;

enum {
    SGM_RECF_SMS_SENT = 1u << 0, /* period-close already duplicated by SMS */
};

#define SGM_RSSI_UNKNOWN INT16_MIN

/* Give an unsynced record a wall-clock time once the clock is known.
 * sync_unix_ms / sync_uptime_ms are the same instant on both clocks.
 * Only valid for records created during the current boot. */
bool sgm_record_backfill(sgm_record_t *rec, int64_t sync_unix_ms, uint64_t sync_uptime_ms);

const char *sgm_event_name(unsigned bit_index);

#ifdef __cplusplus
}
#endif
#endif

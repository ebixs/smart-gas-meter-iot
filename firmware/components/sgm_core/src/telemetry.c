#include "sgm/telemetry.h"

#include <inttypes.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "sgm/jalali.h"

static const char *const EVENT_NAMES[SGM_EVT_COUNT] = {
    "tamper_open",     "tamper_closed",    "counter_restored", "store_empty",     "queue_overflow",
    "implausible_rate", "late_close",      "brownout_reset",   "watchdog_reset",
};

const char *sgm_event_name(unsigned bit_index)
{
    return bit_index < SGM_EVT_COUNT ? EVENT_NAMES[bit_index] : NULL;
}

bool sgm_record_backfill(sgm_record_t *rec, int64_t sync_unix_ms, uint64_t sync_uptime_ms)
{
    if (rec->time_source != SGM_TIME_UNSYNCED || rec->uptime_ms > sync_uptime_ms) {
        return false;
    }
    rec->unix_ms = sync_unix_ms - (int64_t)(sync_uptime_ms - rec->uptime_ms);
    rec->time_source = SGM_TIME_BACKFILLED;
    return true;
}

int sgm_format_utc(int64_t unix_ms, char *out, size_t n)
{
    int64_t secs = sgm_floor_div(unix_ms, 1000);
    int ms = (int)(unix_ms - secs * 1000);
    int32_t days = (int32_t)sgm_floor_div(secs, 86400);
    int sod = (int)(secs - (int64_t)days * 86400);
    sgm_date_t g = sgm_gregorian_from_days(days);
    int len = snprintf(out, n, "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ", g.year, g.month, g.day, sod / 3600,
                       (sod / 60) % 60, sod % 60, ms);
    return (len < 0 || (size_t)len >= n) ? SGM_JSON_NO_SPACE : len;
}

typedef struct {
    char *p;
    size_t left;
    int len;
    int err;
} writer_t;

static void w(writer_t *wr, const char *fmt, ...)
{
    if (wr->err) {
        return;
    }
    va_list ap;
    va_start(ap, fmt);
    int k = vsnprintf(wr->p, wr->left, fmt, ap);
    va_end(ap);
    if (k < 0 || (size_t)k >= wr->left) {
        wr->err = 1;
        return;
    }
    wr->p += k;
    wr->left -= (size_t)k;
    wr->len += k;
}

static int device_id_ok(const char *id)
{
    size_t n = id ? strlen(id) : 0;
    if (n == 0 || n > 64) {
        return 0;
    }
    for (size_t i = 0; i < n; i++) {
        char c = id[i];
        int ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '.' ||
                 c == '_' || c == '-';
        if (!ok) {
            return 0;
        }
    }
    return 1;
}

static const char *record_type_name(uint8_t t)
{
    switch (t) {
    case SGM_REC_PERIOD_CLOSE: return "period_close";
    case SGM_REC_EVENT: return "event";
    default: return "interval";
    }
}

static const char *time_source_name(uint8_t t)
{
    switch (t) {
    case SGM_TIME_NETWORK: return "network";
    case SGM_TIME_SNTP: return "sntp";
    default: return "backfilled";
    }
}

int sgm_telemetry_json(const sgm_record_t *rec, const sgm_device_info_t *dev, char *out, size_t n)
{
    if (!device_id_ok(dev->device_id)) {
        return SGM_JSON_BAD_DEVICE_ID;
    }
    if (rec->time_source == SGM_TIME_UNSYNCED) {
        return SGM_JSON_UNSYNCED;
    }
    char ts[32];
    if (sgm_format_utc(rec->unix_ms, ts, sizeof ts) < 0) {
        return SGM_JSON_NO_SPACE;
    }
    writer_t wr = {out, n, 0, 0};
    /* Field strings below are fixed literals or validated identifiers: no escaping needed. */
    w(&wr, "{\"schema_version\":%d,\"device_id\":\"%s\",\"sequence\":%" PRIu32 ",\"timestamp\":\"%s\"",
      SGM_TELEMETRY_SCHEMA_VERSION, dev->device_id, rec->sequence, ts);
    w(&wr, ",\"uptime_ms\":%" PRIu64 ",\"pulse_count_total\":%" PRIu64 ",\"input_mode\":\"%s\"", rec->uptime_ms,
      rec->pulse_total, dev->input_mode);
    w(&wr, ",\"record_type\":\"%s\",\"time_source\":\"%s\",\"fw_version\":\"%s\"", record_type_name(rec->type),
      time_source_name(rec->time_source), dev->fw_version);
    if (rec->type == SGM_REC_PERIOD_CLOSE) {
        w(&wr, ",\"period\":{\"calendar\":\"jalali\",\"start\":\"%04d/%02d\",\"months\":%d}", rec->period_year,
          rec->period_month, rec->period_months);
    }
    if (rec->events) {
        w(&wr, ",\"events\":[");
        int first = 1;
        for (unsigned b = 0; b < SGM_EVT_COUNT; b++) {
            if (rec->events & (1u << b)) {
                w(&wr, "%s\"%s\"", first ? "" : ",", EVENT_NAMES[b]);
                first = 0;
            }
        }
        w(&wr, "]");
    }
    if (rec->rssi_dbm != SGM_RSSI_UNKNOWN) {
        w(&wr, ",\"rssi_dbm\":%d", rec->rssi_dbm);
    }
    if (rec->supply_mv) {
        w(&wr, ",\"supply_mv\":%u", (unsigned)rec->supply_mv);
    }
    w(&wr, "}");
    return wr.err ? SGM_JSON_NO_SPACE : wr.len;
}

int sgm_telemetry_batch_json(const sgm_record_t *const *recs, size_t count, const sgm_device_info_t *dev,
                             char *out, size_t n, size_t *encoded)
{
    *encoded = 0;
    if (n < 3) {
        return SGM_JSON_NO_SPACE;
    }
    size_t used = 1;
    out[0] = '[';
    for (size_t i = 0; i < count; i++) {
        size_t sep = i ? 1 : 0;
        if (used + sep + 2 > n) {
            break;
        }
        int k = sgm_telemetry_json(recs[i], dev, out + used + sep, n - used - sep - 1); /* keep room for ']' */
        if (k < 0) {
            if (k == SGM_JSON_BAD_DEVICE_ID) {
                return k;
            }
            break;
        }
        if (sep) {
            out[used] = ',';
        }
        used += sep + (size_t)k;
        (*encoded)++;
    }
    out[used++] = ']';
    out[used] = '\0';
    return (int)used;
}

/* Host unit tests for the portable firmware core (gcc/clang, no ESP-IDF). */
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sgm/at.h"
#include "sgm/backoff.h"
#include "sgm/debounce.h"
#include "sgm/jalali.h"
#include "sgm/meter.h"
#include "sgm/period.h"
#include "sgm/queue.h"
#include "sgm/sms.h"
#include "sgm/store.h"
#include "sgm/telemetry.h"

static int g_failures, g_checks;

#define CHECK(cond)                                                                  \
    do {                                                                             \
        g_checks++;                                                                  \
        if (!(cond)) {                                                               \
            g_failures++;                                                            \
            fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #cond); \
        }                                                                            \
    } while (0)
#define CHECK_EQ_INT(a, b)                                                                              \
    do {                                                                                                \
        long long _a = (long long)(a), _b = (long long)(b);                                             \
        g_checks++;                                                                                     \
        if (_a != _b) {                                                                                 \
            g_failures++;                                                                               \
            fprintf(stderr, "%s:%d: %s == %s failed: %lld != %lld\n", __FILE__, __LINE__, #a, #b, _a, _b); \
        }                                                                                               \
    } while (0)
#define CHECK_STR(a, b)                                                                              \
    do {                                                                                             \
        g_checks++;                                                                                  \
        if (strcmp((a), (b)) != 0) {                                                                 \
            g_failures++;                                                                            \
            fprintf(stderr, "%s:%d: strings differ:\n  got:  %s\n  want: %s\n", __FILE__, __LINE__, (a), (b)); \
        }                                                                                            \
    } while (0)

/* ------------------------------------------------------------------ debounce */
static sgm_debounce_cfg_t cfg_ms(void)
{
    sgm_debounce_cfg_t c = {30000, 30000, 5000000};
    return c;
}

static void test_debounce_clean_pulse(void)
{
    sgm_debounce_t d;
    sgm_debounce_cfg_t c = cfg_ms();
    sgm_debounce_init(&d, &c, 1, 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 0, 1000000), 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 1, 1200000), 1); /* 200 ms closure */
}

static void test_debounce_bounce_counts_once(void)
{
    sgm_debounce_t d;
    sgm_debounce_cfg_t c = cfg_ms();
    sgm_debounce_init(&d, &c, 1, 0);
    int64_t t = 1000000;
    int counted = 0;
    /* Closing bounce: 5 short open/close flickers of 200 us. */
    for (int i = 0; i < 5; i++) {
        counted += sgm_debounce_edge(&d, 0, t) > 0;
        counted += sgm_debounce_edge(&d, 1, t + 200) > 0;
        t += 400;
    }
    counted += sgm_debounce_edge(&d, 0, t) > 0;
    t += 150000; /* contact held closed for 150 ms */
    /* Opening bounce, also short. */
    for (int i = 0; i < 4; i++) {
        counted += sgm_debounce_edge(&d, 1, t) > 0;
        counted += sgm_debounce_edge(&d, 0, t + 300) > 0;
        t += 600;
    }
    counted += sgm_debounce_edge(&d, 1, t) > 0;
    CHECK_EQ_INT(counted, 1);
}

static void test_debounce_rejects_spike_and_boot_low(void)
{
    sgm_debounce_t d;
    sgm_debounce_cfg_t c = cfg_ms();
    sgm_debounce_init(&d, &c, 1, 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 0, 1000000), 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 1, 1000050), 0); /* 50 us EMI spike */
    CHECK_EQ_INT(d.glitches, 1);

    sgm_debounce_init(&d, &c, 0, 0); /* contact already closed at boot */
    CHECK_EQ_INT(sgm_debounce_edge(&d, 1, 500000), 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 0, 10000000), 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 1, 10100000), 1);
}

static void test_debounce_flags_fast_pulses(void)
{
    sgm_debounce_t d;
    sgm_debounce_cfg_t c = cfg_ms();
    sgm_debounce_init(&d, &c, 1, 0);
    sgm_debounce_edge(&d, 0, 0);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 1, 100000), 1);
    sgm_debounce_edge(&d, 0, 1000000);
    CHECK_EQ_INT(sgm_debounce_edge(&d, 1, 1100000), 2); /* 1 s apart: faster than Qmax allows */
    CHECK_EQ_INT(d.fast_pulses, 1);
}

/* ------------------------------------------------------------------ jalali */
static void test_jalali_known_dates(void)
{
    sgm_date_t j = sgm_jalali_from_days(sgm_days_from_gregorian(2025, 3, 21));
    CHECK_EQ_INT(j.year, 1404);
    CHECK_EQ_INT(j.month, 1);
    CHECK_EQ_INT(j.day, 1);
    j = sgm_jalali_from_days(sgm_days_from_gregorian(2024, 3, 20));
    CHECK_EQ_INT(j.year * 10000 + j.month * 100 + j.day, 14030101);
    j = sgm_jalali_from_days(sgm_days_from_gregorian(2026, 10, 25));
    CHECK_EQ_INT(j.year * 10000 + j.month * 100 + j.day, 14050803);
    CHECK_EQ_INT(sgm_days_from_gregorian(1970, 1, 1), 0);
    CHECK(sgm_jalali_is_leap(1403));
    CHECK(!sgm_jalali_is_leap(1404));
    CHECK_EQ_INT(sgm_jalali_month_length(1403, 12), 30);
    CHECK_EQ_INT(sgm_jalali_month_length(1404, 12), 29);
}

static void test_jalali_round_trip(void)
{
    int bad = 0;
    for (int32_t d = sgm_days_from_gregorian(1950, 1, 1); d < sgm_days_from_gregorian(2100, 1, 1); d++) {
        sgm_date_t j = sgm_jalali_from_days(d);
        sgm_date_t g = sgm_gregorian_from_days(d);
        if (sgm_days_from_jalali(j.year, j.month, j.day) != d || sgm_days_from_gregorian(g.year, g.month, g.day) != d ||
            j.day < 1 || j.day > sgm_jalali_month_length(j.year, j.month)) {
            bad++;
        }
    }
    CHECK_EQ_INT(bad, 0);
}

/* ------------------------------------------------------------------ periods */
static int64_t unix_of(int y, int mo, int d, int h, int mi)
{
    return (int64_t)sgm_days_from_gregorian(y, mo, d) * 86400 + h * 3600 + mi * 60;
}

static void test_period_boundaries_iran_time(void)
{
    /* Mehr 1405 starts 2026-09-23 00:00 Tehran = 2026-09-22 20:30 UTC. */
    sgm_period_t p = sgm_period_of(unix_of(2026, 9, 22, 20, 29), SGM_TZ_IRAN_S, 3);
    CHECK_EQ_INT(p.year * 100 + p.month, 140504); /* Tir..Shahrivar season */
    p = sgm_period_of(unix_of(2026, 9, 22, 20, 30), SGM_TZ_IRAN_S, 3);
    CHECK_EQ_INT(p.year * 100 + p.month, 140507);
    CHECK_EQ_INT(sgm_period_next_boundary(unix_of(2026, 8, 1, 0, 0), SGM_TZ_IRAN_S, 3), unix_of(2026, 9, 22, 20, 30));
    /* Monthly: Esfand 1404 -> Farvardin 1405 starts 2026-03-21 00:00 Tehran. */
    CHECK_EQ_INT(sgm_period_next_boundary(unix_of(2026, 3, 1, 0, 0), SGM_TZ_IRAN_S, 1), unix_of(2026, 3, 20, 20, 30));
    p = sgm_period_next(sgm_period_of(unix_of(2026, 3, 1, 0, 0), SGM_TZ_IRAN_S, 3));
    CHECK_EQ_INT(p.year * 100 + p.month, 140501);
}

static void test_period_tracker_closes_once(void)
{
    sgm_period_tracker_t t;
    sgm_period_close_t c;
    sgm_period_tracker_init(&t, 3, SGM_TZ_IRAN_S);
    int64_t b = unix_of(2026, 9, 22, 20, 30);
    CHECK(!sgm_period_observe(&t, b - 60, &c));
    CHECK(!sgm_period_observe(&t, b - 1, &c));
    CHECK(sgm_period_observe(&t, b + 5, &c));
    CHECK_EQ_INT(c.closed.year * 100 + c.closed.month, 140504);
    CHECK_EQ_INT(c.boundary_unix, b);
    CHECK(!c.late);
    CHECK(!sgm_period_observe(&t, b + 10, &c));
    CHECK(!sgm_period_observe(&t, b - 100, &c)); /* clock stepped back: nothing reopens */
    CHECK(sgm_period_observe(&t, unix_of(2027, 1, 15, 0, 0), &c)); /* Dey started while "off" */
    CHECK(c.late);
}

/* ------------------------------------------------------------------ store */
typedef struct {
    uint8_t slot[2][SGM_STORE_IMAGE_LEN];
    int present[2];
    int writes;
    int fail_next_write; /* simulate power loss mid-write: slot left corrupted */
} mem_flash_t;

static int mem_read(void *ctx, int slot, uint8_t *buf, size_t len)
{
    mem_flash_t *f = ctx;
    if (!f->present[slot]) return 1;
    memcpy(buf, f->slot[slot], len);
    return 0;
}

static int mem_write(void *ctx, int slot, const uint8_t *buf, size_t len)
{
    mem_flash_t *f = ctx;
    f->writes++;
    memcpy(f->slot[slot], buf, len);
    f->present[slot] = 1;
    if (f->fail_next_write) {
        f->slot[slot][21] ^= 0x5A; /* torn write */
        f->fail_next_write = 0;
        return -1;
    }
    return 0;
}

static void test_store_ab_slots_survive_torn_write(void)
{
    mem_flash_t f;
    memset(&f, 0, sizeof f);
    sgm_store_io_t io = {mem_read, mem_write, &f};
    sgm_persist_t st, got;
    CHECK_EQ_INT(sgm_store_load(&io, &got), SGM_STORE_EMPTY);
    memset(&st, 0, sizeof st);
    st.pulse_total = 41;
    st.sequence = 7;
    sgm_store_save(&io, &st);
    st.pulse_total = 42;
    sgm_store_save(&io, &st);
    CHECK_EQ_INT(sgm_store_load(&io, &got), SGM_STORE_OK);
    CHECK_EQ_INT(got.pulse_total, 42);
    f.fail_next_write = 1;
    st.pulse_total = 43;
    CHECK_EQ_INT(sgm_store_save(&io, &st), SGM_STORE_IO_ERROR);
    CHECK_EQ_INT(sgm_store_load(&io, &got), SGM_STORE_OK);
    CHECK_EQ_INT(got.pulse_total, 42); /* older good copy wins over the torn one */
    CHECK_EQ_INT(sgm_crc32((const uint8_t *)"123456789", 9), 0xCBF43926u);
}

static void test_store_generation_wraps(void)
{
    mem_flash_t f;
    memset(&f, 0, sizeof f);
    sgm_store_io_t io = {mem_read, mem_write, &f};
    sgm_persist_t st, got;
    memset(&st, 0, sizeof st);
    st.generation = 0xFFFFFFFEu;
    st.pulse_total = 1;
    sgm_store_save(&io, &st); /* gen 0xFFFFFFFF */
    st.pulse_total = 2;
    sgm_store_save(&io, &st); /* gen 0 */
    sgm_store_load(&io, &got);
    CHECK_EQ_INT(got.pulse_total, 2);
}

/* ------------------------------------------------------------------ queue */
static void test_queue_keeps_period_close_when_full(void)
{
    sgm_record_t storage[4];
    sgm_queue_t q;
    sgm_queue_init(&q, storage, 4);
    sgm_record_t r;
    memset(&r, 0, sizeof r);
    r.type = SGM_REC_PERIOD_CLOSE;
    r.sequence = 1;
    sgm_queue_push(&q, &r);
    r.type = SGM_REC_INTERVAL;
    for (uint32_t s = 2; s <= 4; s++) {
        r.sequence = s;
        CHECK(sgm_queue_push(&q, &r));
    }
    r.sequence = 5;
    CHECK(!sgm_queue_push(&q, &r)); /* drops seq 2, the oldest interval */
    CHECK_EQ_INT(q.dropped, 1);
    CHECK_EQ_INT(sgm_queue_at(&q, 0)->sequence, 1);
    CHECK_EQ_INT(sgm_queue_at(&q, 1)->sequence, 3);
    CHECK_EQ_INT(sgm_queue_at(&q, 3)->sequence, 5);
    sgm_queue_pop(&q, 2);
    CHECK_EQ_INT(sgm_queue_count(&q), 2);
    CHECK_EQ_INT(sgm_queue_at(&q, 0)->sequence, 4);
    CHECK_EQ_INT(sgm_queue_ack(&q, 4), 1); /* acknowledges by sequence, not by position */
    CHECK_EQ_INT(sgm_queue_at(&q, 0)->sequence, 5);
    CHECK_EQ_INT(sgm_queue_ack(&q, 3), 0);
}

/* ------------------------------------------------------------------ telemetry */
static const sgm_device_info_t DEV = {"sgm-bench-01", "0.3.0", "bench_pulse"};

static void test_utc_format(void)
{
    char buf[32];
    sgm_format_utc(unix_of(2026, 9, 22, 20, 30) * 1000 + 7, buf, sizeof buf);
    CHECK_STR(buf, "2026-09-22T20:30:00.007Z");
    sgm_format_utc(-1, buf, sizeof buf);
    CHECK_STR(buf, "1969-12-31T23:59:59.999Z");
}

static void test_telemetry_json_period_close(void)
{
    sgm_record_t r;
    memset(&r, 0, sizeof r);
    r.sequence = 812;
    r.type = SGM_REC_PERIOD_CLOSE;
    r.time_source = SGM_TIME_NETWORK;
    r.unix_ms = unix_of(2026, 9, 22, 20, 30) * 1000;
    r.uptime_ms = 3600000;
    r.pulse_total = 123456;
    r.events = SGM_EVT_COUNTER_RESTORED | SGM_EVT_LATE_CLOSE;
    r.rssi_dbm = -87;
    r.period_year = 1405;
    r.period_month = 4;
    r.period_months = 3;
    char buf[512];
    int n = sgm_telemetry_json(&r, &DEV, buf, sizeof buf);
    CHECK(n > 0);
    CHECK_STR(buf, "{\"schema_version\":2,\"device_id\":\"sgm-bench-01\",\"sequence\":812,"
                   "\"timestamp\":\"2026-09-22T20:30:00.000Z\",\"uptime_ms\":3600000,\"pulse_count_total\":123456,"
                   "\"input_mode\":\"bench_pulse\",\"record_type\":\"period_close\",\"time_source\":\"network\","
                   "\"fw_version\":\"0.3.0\",\"period\":{\"calendar\":\"jalali\",\"start\":\"1405/04\",\"months\":3},"
                   "\"events\":[\"counter_restored\",\"late_close\"],\"rssi_dbm\":-87}");
    CHECK_EQ_INT(sgm_telemetry_json(&r, &DEV, buf, 40), SGM_JSON_NO_SPACE);
    r.time_source = SGM_TIME_UNSYNCED;
    CHECK_EQ_INT(sgm_telemetry_json(&r, &DEV, buf, sizeof buf), SGM_JSON_UNSYNCED);
    sgm_device_info_t bad = {"bad\"id", "0", "bench_pulse"};
    r.time_source = SGM_TIME_SNTP;
    CHECK_EQ_INT(sgm_telemetry_json(&r, &bad, buf, sizeof buf), SGM_JSON_BAD_DEVICE_ID);
}

static void test_telemetry_batch_stops_cleanly(void)
{
    sgm_record_t a, b;
    memset(&a, 0, sizeof a);
    a.sequence = 1;
    a.time_source = SGM_TIME_SNTP;
    a.unix_ms = 1700000000000;
    a.rssi_dbm = SGM_RSSI_UNKNOWN;
    b = a;
    b.sequence = 2;
    const sgm_record_t *recs[] = {&a, &b};
    char buf[1024];
    size_t enc;
    int n = sgm_telemetry_batch_json(recs, 2, &DEV, buf, sizeof buf, &enc);
    CHECK(n > 0);
    CHECK_EQ_INT(enc, 2);
    CHECK(buf[0] == '[' && buf[n - 1] == ']' && (size_t)n == strlen(buf));
    n = sgm_telemetry_batch_json(recs, 2, &DEV, buf, 260, &enc); /* room for one record only */
    CHECK_EQ_INT(enc, 1);
    CHECK(buf[n - 1] == ']' && strchr(buf, '}') == strrchr(buf, '}'));
}

static void test_sms_period_close(void)
{
    sgm_record_t r;
    memset(&r, 0, sizeof r);
    r.type = SGM_REC_PERIOD_CLOSE;
    r.time_source = SGM_TIME_NETWORK;
    r.unix_ms = unix_of(2026, 9, 22, 20, 30) * 1000;
    r.pulse_total = 123456;
    r.sequence = 812;
    r.period_year = 1405;
    r.period_month = 4;
    r.period_months = 3;
    char buf[200];
    int n = sgm_sms_period_close(&r, &DEV, buf, sizeof buf);
    CHECK(n > 0 && n <= SGM_SMS_MAX);
    CHECK_STR(buf, "SGM1 sgm-bench-01 P=1405/04x3 C=123456 S=812 T=20260922T2030Z");
}

/* ------------------------------------------------------------------ backoff */
static void test_backoff_grows_and_caps(void)
{
    sgm_backoff_t b;
    sgm_backoff_init(&b, 1000, 60000, 42);
    uint32_t prev_hi = 0;
    for (int k = 0; k < 12; k++) {
        uint32_t d = sgm_backoff_next(&b);
        uint32_t full = (uint32_t)(1000u << k);
        if (full > 60000) full = 60000;
        CHECK(d >= full / 2 && d <= full);
        prev_hi = full;
    }
    CHECK_EQ_INT(prev_hi, 60000);
    sgm_backoff_reset(&b);
    CHECK(sgm_backoff_next(&b) <= 1000);
}

/* ------------------------------------------------------------------ AT parser */
static void test_at_parser(void)
{
    sgm_at_result_t r;
    CHECK_EQ_INT(sgm_at_parse_line("OK", &r), SGM_AT_OK);
    CHECK_EQ_INT(sgm_at_parse_line("+CME ERROR: 703", &r), SGM_AT_CME_ERROR);
    CHECK_EQ_INT(r.a, 703);
    CHECK_EQ_INT(sgm_at_parse_line("+CSQ: 18,99", &r), SGM_AT_CSQ);
    CHECK_EQ_INT(sgm_csq_to_dbm(r.a), -77);
    CHECK_EQ_INT(sgm_csq_to_dbm(99), SGM_RSSI_UNKNOWN);
    CHECK_EQ_INT(sgm_at_parse_line("+CEREG: 0,5", &r), SGM_AT_REG);
    CHECK_EQ_INT(r.a, 5);
    CHECK_EQ_INT(r.b, 1);
    CHECK_EQ_INT(sgm_at_parse_line("+CEREG: 2", &r), SGM_AT_REG); /* URC: searching */
    CHECK_EQ_INT(r.a, 2);
    CHECK_EQ_INT(r.b, 0);
    CHECK_EQ_INT(sgm_at_parse_line("+CEREG: 1,\"1A2B\",\"01C3D4E5\",7", &r), SGM_AT_REG);
    CHECK_EQ_INT(r.a, 1);
    CHECK_EQ_INT(sgm_at_parse_line("+CEREG: 2,1,\"1A2B\",\"01C3D4E5\",7", &r), SGM_AT_REG);
    CHECK_EQ_INT(r.a, 1);
    /* Tehran local 00:00:05 on 2026-09-23 with +14 quarter hours (+03:30). */
    CHECK_EQ_INT(sgm_at_parse_line("+CCLK: \"26/09/23,00:00:05+14\"", &r), SGM_AT_CCLK);
    CHECK_EQ_INT(r.unix_s, unix_of(2026, 9, 22, 20, 30) + 5);
    CHECK_EQ_INT(sgm_at_parse_line("+QHTTPPOST: 0,201,57", &r), SGM_AT_HTTP_RESULT);
    CHECK_EQ_INT(r.b, 201);
    CHECK_EQ_INT(sgm_at_parse_line("+CMGS: 17", &r), SGM_AT_CMGS);
    CHECK_EQ_INT(sgm_at_parse_line("RDY", &r), SGM_AT_OTHER);

    sgm_at_linebuf_t lb;
    sgm_at_linebuf_init(&lb);
    const char *stream = "\r\nOK\r\n> ";
    int lines = 0;
    char seen[2][sizeof lb.buf];
    for (const char *p = stream; *p; p++) {
        if (sgm_at_linebuf_feed(&lb, *p)) {
            snprintf(seen[lines++], sizeof seen[0], "%s", lb.buf);
        }
    }
    CHECK_EQ_INT(lines, 2);
    CHECK_STR(seen[0], "OK");
    CHECK_EQ_INT(sgm_at_parse_line(seen[1], &r), SGM_AT_SMS_PROMPT);
}

/* ------------------------------------------------------------------ meter (integration) */
static void test_meter_self_reading_across_season(void)
{
    mem_flash_t f;
    memset(&f, 0, sizeof f);
    sgm_record_t storage[32];
    sgm_queue_t q;
    sgm_queue_init(&q, storage, 32);
    sgm_meter_cfg_t cfg = {{mem_read, mem_write, &f}, {1, 900000}, &q, 3, SGM_TZ_IRAN_S, 0};
    sgm_meter_t m;
    sgm_meter_boot(&m, &cfg, 100);
    CHECK_EQ_INT(sgm_queue_count(&q), 1);
    CHECK(sgm_queue_at(&q, 0)->events & SGM_EVT_STORE_EMPTY);

    /* Two pulses before the clock is known; network time arrives later. */
    sgm_meter_pulse(&m, 1000, false);
    sgm_meter_pulse(&m, 9000, false);
    int64_t boundary_ms = unix_of(2026, 9, 22, 20, 30) * 1000;
    sgm_meter_set_time(&m, boundary_ms - 60000, 10000, SGM_TIME_NETWORK); /* one minute before Mehr */
    CHECK_EQ_INT(sgm_queue_at(&q, 0)->time_source, SGM_TIME_BACKFILLED);
    CHECK_EQ_INT(sgm_queue_at(&q, 0)->unix_ms, boundary_ms - 60000 - 9900);

    sgm_meter_pulse(&m, 30000, false);  /* 30 s before the boundary */
    sgm_meter_pulse(&m, 80000, false);  /* 10 s after: closes the season first */
    CHECK_EQ_INT(sgm_queue_count(&q), 2);
    sgm_record_t *close = sgm_queue_at(&q, 1);
    CHECK_EQ_INT(close->type, SGM_REC_PERIOD_CLOSE);
    CHECK_EQ_INT(close->pulse_total, 3); /* the 4th pulse belongs to the new season */
    CHECK_EQ_INT(close->unix_ms, boundary_ms);
    CHECK_EQ_INT(close->period_year * 100 + close->period_month, 140504);
    CHECK_EQ_INT(close->sequence, 2);
    CHECK_EQ_INT(m.st.pulse_total, 4);

    /* Power cut and reboot: the counter, sequence and open period come back. */
    sgm_record_t storage2[8];
    sgm_queue_t q2;
    sgm_queue_init(&q2, storage2, 8);
    cfg.queue = &q2;
    cfg.boot_events = SGM_EVT_BROWNOUT_RESET;
    sgm_meter_t m2;
    sgm_meter_boot(&m2, &cfg, 50);
    CHECK_EQ_INT(m2.st.pulse_total, 4);
    CHECK_EQ_INT(sgm_queue_at(&q2, 0)->sequence, 3);
    CHECK(sgm_queue_at(&q2, 0)->events & SGM_EVT_COUNTER_RESTORED);
    CHECK(sgm_queue_at(&q2, 0)->events & SGM_EVT_BROWNOUT_RESET);
    sgm_meter_set_time(&m2, boundary_ms + 3600000, 1000, SGM_TIME_NETWORK);
    CHECK_EQ_INT(sgm_queue_count(&q2), 1); /* same season: no second close */
    sgm_meter_snapshot(&m2, 2000);
    CHECK_EQ_INT(sgm_queue_at(&q2, 1)->sequence, 4);
    CHECK(sgm_queue_at(&q2, 1)->unix_ms >= sgm_queue_at(&q2, 0)->unix_ms);
}

int main(void)
{
    test_debounce_clean_pulse();
    test_debounce_bounce_counts_once();
    test_debounce_rejects_spike_and_boot_low();
    test_debounce_flags_fast_pulses();
    test_jalali_known_dates();
    test_jalali_round_trip();
    test_period_boundaries_iran_time();
    test_period_tracker_closes_once();
    test_store_ab_slots_survive_torn_write();
    test_store_generation_wraps();
    test_queue_keeps_period_close_when_full();
    test_utc_format();
    test_telemetry_json_period_close();
    test_telemetry_batch_stops_cleanly();
    test_sms_period_close();
    test_backoff_grows_and_caps();
    test_at_parser();
    test_meter_self_reading_across_season();
    printf("%d checks, %d failures\n", g_checks, g_failures);
    return g_failures ? EXIT_FAILURE : EXIT_SUCCESS;
}

/*
 * Host CLI around the firmware core, used for cross-checks against the
 * Python analytics package and the telemetry schema:
 *   sgm_host jalali FROM_DAYS TO_DAYS     -> "days jy jm jd" per line
 *   sgm_host boundaries UNIX_S N MONTHS   -> next N period boundaries (unix s)
 *   sgm_host demo                         -> JSONL telemetry for a simulated season change
 */
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sgm/jalali.h"
#include "sgm/meter.h"
#include "sgm/telemetry.h"

static uint8_t g_flash[2][SGM_STORE_IMAGE_LEN];
static int g_present[2];

static int fread_slot(void *ctx, int slot, uint8_t *buf, size_t len)
{
    (void)ctx;
    if (!g_present[slot]) return 1;
    memcpy(buf, g_flash[slot], len);
    return 0;
}

static int fwrite_slot(void *ctx, int slot, const uint8_t *buf, size_t len)
{
    (void)ctx;
    memcpy(g_flash[slot], buf, len);
    g_present[slot] = 1;
    return 0;
}

static int demo(void)
{
    static sgm_record_t storage[64];
    sgm_queue_t q;
    sgm_queue_init(&q, storage, 64);
    sgm_meter_cfg_t cfg = {{fread_slot, fwrite_slot, NULL}, {1, 900000}, &q, 3, SGM_TZ_IRAN_S, 0};
    sgm_meter_t m;
    sgm_meter_boot(&m, &cfg, 120);
    m.rssi_dbm = -79;
    /* Boundary of Mehr 1405 = 2026-09-22T20:30Z. Start the clock 3 hours before. */
    int64_t boundary_ms = ((int64_t)sgm_days_from_gregorian(2026, 9, 22) * 86400 + 20 * 3600 + 30 * 60) * 1000;
    sgm_meter_set_time(&m, boundary_ms - 3 * 3600000, 5000, SGM_TIME_NETWORK);
    uint64_t up = 5000;
    for (int hour = 0; hour < 6; hour++) {
        for (int k = 0; k < 12 + hour * 3; k++) { /* evening use rising, one pulse = 0.01 m3 */
            up += 3600000 / (uint64_t)(12 + hour * 3);
            sgm_meter_pulse(&m, up, false);
        }
        sgm_meter_snapshot(&m, up);
    }
    sgm_meter_event(&m, SGM_EVT_TAMPER_OPEN, up + 1000);
    const sgm_device_info_t dev = {"sgm-bench-01", "0.3.0-host", "simulated"};
    char line[512];
    for (uint16_t i = 0; i < sgm_queue_count(&q); i++) {
        if (sgm_telemetry_json(sgm_queue_at(&q, i), &dev, line, sizeof line) < 0) {
            fprintf(stderr, "record %u could not be encoded\n", i);
            return 1;
        }
        puts(line);
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc == 4 && strcmp(argv[1], "jalali") == 0) {
        for (int32_t d = atoi(argv[2]); d < atoi(argv[3]); d++) {
            sgm_date_t j = sgm_jalali_from_days(d);
            printf("%" PRId32 " %d %d %d\n", d, j.year, j.month, j.day);
        }
        return 0;
    }
    if (argc == 5 && strcmp(argv[1], "boundaries") == 0) {
        int64_t t = strtoll(argv[2], NULL, 10);
        int n = atoi(argv[3]), months = atoi(argv[4]);
        for (int i = 0; i < n; i++) {
            t = sgm_period_next_boundary(t, SGM_TZ_IRAN_S, months);
            printf("%" PRId64 "\n", t);
        }
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "demo") == 0) {
        return demo();
    }
    fprintf(stderr, "usage: sgm_host jalali FROM TO | boundaries UNIX_S N MONTHS | demo\n");
    return 2;
}

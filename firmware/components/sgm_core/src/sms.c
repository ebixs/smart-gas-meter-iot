#include "sgm/sms.h"

#include <inttypes.h>
#include <stdio.h>

#include "sgm/jalali.h"

int sgm_sms_period_close(const sgm_record_t *rec, const sgm_device_info_t *dev, char *out, size_t n)
{
    if (rec->type != SGM_REC_PERIOD_CLOSE) {
        return SGM_JSON_NO_SPACE;
    }
    if (rec->time_source == SGM_TIME_UNSYNCED) {
        return SGM_JSON_UNSYNCED;
    }
    int64_t secs = sgm_floor_div(rec->unix_ms, 1000);
    int32_t days = (int32_t)sgm_floor_div(secs, 86400);
    int sod = (int)(secs - (int64_t)days * 86400);
    sgm_date_t g = sgm_gregorian_from_days(days);
    int len = snprintf(out, n, "SGM1 %s P=%04d/%02dx%d C=%" PRIu64 " S=%" PRIu32 " T=%04d%02d%02dT%02d%02dZ",
                       dev->device_id, rec->period_year, rec->period_month, rec->period_months, rec->pulse_total,
                       rec->sequence, g.year, g.month, g.day, sod / 3600, (sod / 60) % 60);
    if (len < 0 || (size_t)len >= n || len > SGM_SMS_MAX) {
        return SGM_JSON_NO_SPACE;
    }
    return len;
}

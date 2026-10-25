#include "sgm/period.h"

#include "sgm/jalali.h"

#define DAY_S 86400

static int first_month_of(int month, int months)
{
    return ((month - 1) / months) * months + 1;
}

sgm_period_t sgm_period_of(int64_t unix_s, int32_t tz_offset_s, int months)
{
    int32_t days = (int32_t)sgm_floor_div(unix_s + tz_offset_s, DAY_S);
    sgm_date_t j = sgm_jalali_from_days(days);
    sgm_period_t p = {j.year, (int8_t)first_month_of(j.month, months), (int8_t)months};
    return p;
}

int64_t sgm_period_start_unix(sgm_period_t p, int32_t tz_offset_s)
{
    return (int64_t)sgm_days_from_jalali(p.year, p.month, 1) * DAY_S - tz_offset_s;
}

sgm_period_t sgm_period_next(sgm_period_t p)
{
    int m = p.month + p.months;
    if (m > 12) {
        p.year++;
        m -= 12;
    }
    p.month = (int8_t)m;
    return p;
}

int64_t sgm_period_next_boundary(int64_t unix_s, int32_t tz_offset_s, int months)
{
    return sgm_period_start_unix(sgm_period_next(sgm_period_of(unix_s, tz_offset_s, months)), tz_offset_s);
}

bool sgm_period_equal(sgm_period_t a, sgm_period_t b)
{
    return a.year == b.year && a.month == b.month && a.months == b.months;
}

void sgm_period_tracker_init(sgm_period_tracker_t *t, int months, int32_t tz_offset_s)
{
    t->valid = false;
    t->months = months;
    t->tz_offset_s = tz_offset_s;
    t->late_after_s = 600;
}

void sgm_period_tracker_restore(sgm_period_tracker_t *t, sgm_period_t open_period)
{
    if (open_period.months == t->months && open_period.month >= 1 && open_period.month <= 12) {
        t->current = open_period;
        t->valid = true;
    }
}

bool sgm_period_observe(sgm_period_tracker_t *t, int64_t unix_s, sgm_period_close_t *out)
{
    sgm_period_t now = sgm_period_of(unix_s, t->tz_offset_s, t->months);
    if (!t->valid) {
        t->current = now;
        t->valid = true;
        return false;
    }
    if (sgm_period_equal(now, t->current)) {
        return false;
    }
    int64_t current_start = sgm_period_start_unix(t->current, t->tz_offset_s);
    if (unix_s < current_start) {
        return false; /* clock stepped backwards: never close a period twice */
    }
    out->closed = t->current;
    out->boundary_unix = sgm_period_start_unix(sgm_period_next(t->current), t->tz_offset_s);
    out->late = (unix_s - out->boundary_unix) > t->late_after_s;
    t->current = now; /* periods skipped while powered off are folded into one late close */
    return true;
}

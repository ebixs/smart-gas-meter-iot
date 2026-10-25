/*
 * Jalali (Solar Hijri) calendar, integer-only port of the jalaali-js
 * algorithm (Borkowski break years). Same algorithm as the analytics
 * package (analytics/sgm_analytics/jalali.py), so device and server agree
 * on every billing-period boundary.
 */
#ifndef SGM_JALALI_H
#define SGM_JALALI_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    int16_t year;
    int8_t month; /* 1..12 */
    int8_t day;   /* 1..31 */
} sgm_date_t;

/* Days since 1970-01-01 (proleptic Gregorian) <-> calendar dates. */
int32_t sgm_days_from_gregorian(int y, int m, int d);
sgm_date_t sgm_gregorian_from_days(int32_t days);

int32_t sgm_days_from_jalali(int jy, int jm, int jd);
sgm_date_t sgm_jalali_from_days(int32_t days);

bool sgm_jalali_is_leap(int jy);
int sgm_jalali_month_length(int jy, int jm);

/* Floor division helper for converting signed seconds to days. */
static inline int64_t sgm_floor_div(int64_t a, int64_t b)
{
    int64_t q = a / b;
    return (a % b != 0 && ((a < 0) != (b < 0))) ? q - 1 : q;
}

#ifdef __cplusplus
}
#endif
#endif

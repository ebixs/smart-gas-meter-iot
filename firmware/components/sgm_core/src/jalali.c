#include "sgm/jalali.h"

/* Julian Day Number of 1970-01-01. */
#define JDN_UNIX_EPOCH 2440588

static const int16_t BREAKS[] = {-61,  9,    38,   199,  426,  686,  756,  818,  1111, 1181,
                                 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178};
#define NBREAKS ((int)(sizeof(BREAKS) / sizeof(BREAKS[0])))

/* C division truncates toward zero, matching jalaali-js's ~~(a / b). */
static int32_t idiv(int32_t a, int32_t b) { return a / b; }
static int32_t imod(int32_t a, int32_t b) { return a - (a / b) * b; }

typedef struct {
    int32_t leap; /* 0 = leap year */
    int32_t gy;
    int32_t march; /* Gregorian day in March of Farvardin 1 */
} jal_cal_t;

static jal_cal_t jal_cal(int32_t jy)
{
    jal_cal_t r;
    int32_t gy = jy + 621, leap_j = -14, jp = BREAKS[0], jm, jump = 0, n;
    for (int i = 1; i < NBREAKS; i++) {
        jm = BREAKS[i];
        jump = jm - jp;
        if (jy < jm) {
            break;
        }
        leap_j = leap_j + idiv(jump, 33) * 8 + idiv(imod(jump, 33), 4);
        jp = jm;
    }
    n = jy - jp;
    leap_j = leap_j + idiv(n, 33) * 8 + idiv(imod(n, 33) + 3, 4);
    if (imod(jump, 33) == 4 && jump - n == 4) {
        leap_j += 1;
    }
    int32_t leap_g = idiv(gy, 4) - idiv((idiv(gy, 100) + 1) * 3, 4) - 150;
    r.march = 20 + leap_j - leap_g;
    r.gy = gy;
    if (jump - n < 6) {
        n = n - jump + idiv(jump + 4, 33) * 33;
    }
    int32_t leap = imod(imod(n + 1, 33) - 1, 4);
    if (leap == -1) {
        leap = 4;
    }
    r.leap = leap;
    return r;
}

static int32_t g2d(int32_t gy, int32_t gm, int32_t gd)
{
    int32_t d = idiv((gy + idiv(gm - 8, 6) + 100100) * 1461, 4) + idiv(153 * imod(gm + 9, 12) + 2, 5) + gd - 34840408;
    return d - idiv(idiv(gy + 100100 + idiv(gm - 8, 6), 100) * 3, 4) + 752;
}

static sgm_date_t d2g(int32_t jdn)
{
    int32_t j = 4 * jdn + 139361631;
    j = j + idiv(idiv(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
    int32_t i = idiv(imod(j, 1461), 4) * 5 + 308;
    sgm_date_t out;
    out.day = (int8_t)(idiv(imod(i, 153), 5) + 1);
    out.month = (int8_t)(imod(idiv(i, 153), 12) + 1);
    out.year = (int16_t)(idiv(j, 1461) - 100100 + idiv(8 - out.month, 6));
    return out;
}

int32_t sgm_days_from_gregorian(int y, int m, int d) { return g2d(y, m, d) - JDN_UNIX_EPOCH; }

sgm_date_t sgm_gregorian_from_days(int32_t days) { return d2g(days + JDN_UNIX_EPOCH); }

int32_t sgm_days_from_jalali(int jy, int jm, int jd)
{
    jal_cal_t r = jal_cal(jy);
    int32_t jdn = g2d(r.gy, 3, r.march) + (jm - 1) * 31 - idiv(jm, 7) * (jm - 7) + jd - 1;
    return jdn - JDN_UNIX_EPOCH;
}

sgm_date_t sgm_jalali_from_days(int32_t days)
{
    int32_t jdn = days + JDN_UNIX_EPOCH;
    int32_t gy = d2g(jdn).year;
    int32_t jy = gy - 621;
    jal_cal_t r = jal_cal(jy);
    int32_t k = jdn - g2d(gy, 3, r.march);
    sgm_date_t out;
    if (k >= 0) {
        if (k <= 185) {
            out.year = (int16_t)jy;
            out.month = (int8_t)(1 + idiv(k, 31));
            out.day = (int8_t)(imod(k, 31) + 1);
            return out;
        }
        k -= 186;
    } else {
        jy -= 1;
        k += 179;
        if (r.leap == 1) {
            k += 1;
        }
    }
    out.year = (int16_t)jy;
    out.month = (int8_t)(7 + idiv(k, 30));
    out.day = (int8_t)(imod(k, 30) + 1);
    return out;
}

bool sgm_jalali_is_leap(int jy) { return jal_cal(jy).leap == 0; }

int sgm_jalali_month_length(int jy, int jm)
{
    if (jm <= 6) {
        return 31;
    }
    if (jm <= 11) {
        return 30;
    }
    return sgm_jalali_is_leap(jy) ? 30 : 29;
}

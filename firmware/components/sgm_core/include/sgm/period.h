/*
 * Billing-period self-reading ("خودخوان"): the device freezes its own counter
 * at every Jalali period boundary in Iran local time, so the bill does not
 * depend on when a reading happens to arrive.
 *
 * Periods start at 00:00 local time on day 1 of a Jalali month. Seasonal
 * periods start on months 1, 4, 7 and 10 (Farvardin, Tir, Mehr, Dey).
 * Iran has used a fixed UTC+03:30 offset since 1402 (no daylight saving).
 */
#ifndef SGM_PERIOD_H
#define SGM_PERIOD_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SGM_TZ_IRAN_S 12600 /* +03:30 */

typedef struct {
    int16_t year;
    int8_t month;  /* first month of the period */
    int8_t months; /* 1 = monthly, 3 = seasonal */
} sgm_period_t;

sgm_period_t sgm_period_of(int64_t unix_s, int32_t tz_offset_s, int months);
int64_t sgm_period_start_unix(sgm_period_t p, int32_t tz_offset_s);
sgm_period_t sgm_period_next(sgm_period_t p);
/* Unix time of the first boundary strictly after unix_s. */
int64_t sgm_period_next_boundary(int64_t unix_s, int32_t tz_offset_s, int months);
bool sgm_period_equal(sgm_period_t a, sgm_period_t b);

typedef struct {
    sgm_period_t current;
    bool valid;
    int32_t tz_offset_s;
    int months;
    int64_t late_after_s; /* a close observed later than this past the boundary is "late" */
} sgm_period_tracker_t;

typedef struct {
    sgm_period_t closed;
    int64_t boundary_unix;
    bool late;
} sgm_period_close_t;

void sgm_period_tracker_init(sgm_period_tracker_t *t, int months, int32_t tz_offset_s);
/* Restore the period that was open before a reset (from flash). */
void sgm_period_tracker_restore(sgm_period_tracker_t *t, sgm_period_t open_period);

/*
 * Call with the current wall-clock time BEFORE applying a new pulse, and from
 * a timer armed at sgm_period_next_boundary(). Returns true and fills *out
 * when a period closed; the caller freezes the counter value it holds at that
 * moment into a period-close record.
 */
bool sgm_period_observe(sgm_period_tracker_t *t, int64_t unix_s, sgm_period_close_t *out);

#ifdef __cplusplus
}
#endif
#endif

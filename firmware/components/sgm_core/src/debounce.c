#include "sgm/debounce.h"

#include <string.h>

void sgm_debounce_init(sgm_debounce_t *d, const sgm_debounce_cfg_t *cfg, int initial_level, int64_t now_us)
{
    memset(d, 0, sizeof(*d));
    d->cfg = *cfg;
    if (initial_level == 0) {
        d->in_low = true;
        d->counted = true; /* closure began before we were watching */
        d->low_start_us = now_us;
    }
}

int sgm_debounce_edge(sgm_debounce_t *d, int level, int64_t t_us)
{
    if (level == 0) {
        if (d->in_low) {
            return 0; /* repeated edge report */
        }
        d->in_low = true;
        if (d->have_rise && (t_us - d->last_rise_us) < (int64_t)d->cfg.min_high_us) {
            return 0; /* bounce: resume the same closure, keep start and counted flag */
        }
        d->low_start_us = t_us;
        d->counted = false;
        return 0;
    }

    if (!d->in_low) {
        return 0;
    }
    d->in_low = false;
    d->last_rise_us = t_us;
    d->have_rise = true;
    if (d->counted) {
        return 0;
    }
    if ((t_us - d->low_start_us) < (int64_t)d->cfg.min_low_us) {
        d->glitches++;
        return 0;
    }
    d->counted = true;
    int result = 1;
    if (d->have_count && (t_us - d->last_count_us) < (int64_t)d->cfg.min_period_us) {
        d->fast_pulses++;
        result = 2;
    }
    d->have_count = true;
    d->last_count_us = t_us;
    return result;
}

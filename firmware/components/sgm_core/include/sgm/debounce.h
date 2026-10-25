/*
 * Edge-driven pulse qualifier for a dry-contact (reed) pulse output.
 *
 * The pin idles high (pull-up) and the contact pulls it low. The GPIO ISR
 * passes every edge with a microsecond timestamp; contact bounce produces
 * bursts of edges that this state machine merges into one pulse:
 *   - a low phase must last at least min_low_us to count;
 *   - a high gap shorter than min_high_us is treated as bounce inside the
 *     same low phase, so one closure can never be counted twice.
 * Hardware PCNT glitch filters top out around 13 us on ESP32-S3, far below
 * reed bounce (ms), which is why qualification happens in software.
 */
#ifndef SGM_DEBOUNCE_H
#define SGM_DEBOUNCE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t min_low_us;    /* shortest closure accepted as a pulse */
    uint32_t min_high_us;   /* shortest open gap that separates two closures */
    uint32_t min_period_us; /* pulses closer than this are flagged implausible */
} sgm_debounce_cfg_t;

typedef struct {
    sgm_debounce_cfg_t cfg;
    int64_t low_start_us;
    int64_t last_rise_us;
    int64_t last_count_us;
    bool in_low;
    bool counted;
    bool have_rise;
    bool have_count;
    uint32_t glitches;     /* low phases rejected as too short */
    uint32_t fast_pulses;  /* accepted pulses that violated min_period_us */
} sgm_debounce_t;

/* Defaults sized for a G4 diaphragm meter with 0.01 m3/pulse:
 * Qmax 6 m3/h -> 600 pulses/h -> 6 s per pulse; 20% margin -> 5 s. */
#define SGM_DEBOUNCE_DEFAULT_MIN_LOW_US 30000u
#define SGM_DEBOUNCE_DEFAULT_MIN_HIGH_US 30000u
#define SGM_DEBOUNCE_DEFAULT_MIN_PERIOD_US 5000000u

/* initial_level is the pin level at start. Starting low never counts a pulse:
 * the start of that closure was not observed. */
void sgm_debounce_init(sgm_debounce_t *d, const sgm_debounce_cfg_t *cfg, int initial_level, int64_t now_us);

/* Feed one edge (level = new pin level). Returns 1 when a pulse is qualified,
 * 2 when it is qualified but faster than min_period_us, 0 otherwise. */
int sgm_debounce_edge(sgm_debounce_t *d, int level, int64_t t_us);

#ifdef __cplusplus
}
#endif
#endif

#include "sgm/meter.h"

#include "sgm/jalali.h"

#include <string.h>

static void save(sgm_meter_t *m, uint64_t uptime_ms)
{
    if (sgm_store_save(&m->io, &m->st) != SGM_STORE_OK) {
        m->store_errors++;
        return;
    }
    m->unsaved_pulses = 0;
    m->last_save_uptime_ms = uptime_ms;
}

bool sgm_meter_now(const sgm_meter_t *m, uint64_t uptime_ms, int64_t *unix_ms)
{
    if (!m->synced) {
        return false;
    }
    *unix_ms = m->sync_unix_ms + (int64_t)uptime_ms - (int64_t)m->sync_uptime_ms;
    return true;
}

static void enqueue(sgm_meter_t *m, uint8_t type, uint16_t events, int64_t unix_ms, uint64_t uptime_ms,
                    const sgm_period_t *period)
{
    sgm_record_t r;
    memset(&r, 0, sizeof r);
    r.sequence = ++m->st.sequence;
    r.type = type;
    r.events = (uint16_t)(events | m->pending_events);
    r.uptime_ms = uptime_ms;
    r.pulse_total = m->st.pulse_total;
    r.rssi_dbm = m->rssi_dbm;
    r.supply_mv = m->supply_mv;
    if (m->synced) {
        if (unix_ms < m->last_record_unix_ms) {
            unix_ms = m->last_record_unix_ms;
        }
        r.unix_ms = unix_ms;
        r.time_source = m->time_source;
        m->last_record_unix_ms = unix_ms;
    } else {
        r.time_source = SGM_TIME_UNSYNCED;
    }
    if (period) {
        r.period_year = period->year;
        r.period_month = (uint8_t)period->month;
        r.period_months = (uint8_t)period->months;
    }
    save(m, uptime_ms); /* the sequence must be durable before the record can leave */
    m->pending_events = 0;
    if (!sgm_queue_push(m->queue, &r)) {
        m->pending_events |= SGM_EVT_QUEUE_OVERFLOW;
    }
}

static void check_period(sgm_meter_t *m, uint64_t uptime_ms)
{
    int64_t now_ms;
    if (!sgm_meter_now(m, uptime_ms, &now_ms)) {
        return;
    }
    sgm_period_close_t c;
    if (!sgm_period_observe(&m->periods, sgm_floor_div(now_ms, 1000), &c)) {
        if (!sgm_period_equal(m->st.open_period, m->periods.current)) {
            m->st.open_period = m->periods.current; /* first period after sync */
            save(m, uptime_ms);
        }
        return;
    }
    m->st.open_period = m->periods.current;
    /* On time: stamp the boundary itself. Late (device was off or unsynced):
     * stamp the observation time and say so; the counter is still exact for
     * "everything up to now", just not for the boundary. */
    int64_t ts = c.late ? now_ms : c.boundary_unix * 1000;
    enqueue(m, SGM_REC_PERIOD_CLOSE, c.late ? SGM_EVT_LATE_CLOSE : 0, ts, uptime_ms, &c.closed);
}

void sgm_meter_boot(sgm_meter_t *m, const sgm_meter_cfg_t *cfg, uint64_t uptime_ms)
{
    memset(m, 0, sizeof(*m));
    m->io = cfg->io;
    m->policy = cfg->policy;
    m->queue = cfg->queue;
    m->rssi_dbm = SGM_RSSI_UNKNOWN;
    sgm_period_tracker_init(&m->periods, cfg->period_months, cfg->tz_offset_s);

    uint16_t events = cfg->boot_events;
    if (sgm_store_load(&m->io, &m->st) == SGM_STORE_OK) {
        events |= SGM_EVT_COUNTER_RESTORED;
        sgm_period_tracker_restore(&m->periods, m->st.open_period);
    } else {
        events |= SGM_EVT_STORE_EMPTY;
    }
    m->st.boot_count++;
    enqueue(m, SGM_REC_EVENT, events, 0, uptime_ms, NULL);
}

void sgm_meter_set_time(sgm_meter_t *m, int64_t unix_ms, uint64_t uptime_ms, uint8_t source)
{
    m->synced = true;
    m->time_source = source;
    m->sync_unix_ms = unix_ms;
    m->sync_uptime_ms = uptime_ms;
    for (uint16_t i = 0; i < sgm_queue_count(m->queue); i++) {
        sgm_record_t *r = sgm_queue_at(m->queue, i);
        if (sgm_record_backfill(r, unix_ms, uptime_ms) && r->unix_ms > m->last_record_unix_ms) {
            m->last_record_unix_ms = r->unix_ms;
        }
    }
    check_period(m, uptime_ms);
}

void sgm_meter_pulse(sgm_meter_t *m, uint64_t uptime_ms, bool implausible)
{
    check_period(m, uptime_ms); /* close the period with the count BEFORE this pulse */
    m->st.pulse_total++;
    m->unsaved_pulses++;
    if (implausible) {
        m->pending_events |= SGM_EVT_IMPLAUSIBLE_RATE;
    }
    if (sgm_store_should_commit(&m->policy, m->unsaved_pulses, uptime_ms - m->last_save_uptime_ms)) {
        save(m, uptime_ms);
    }
}

void sgm_meter_tick(sgm_meter_t *m, uint64_t uptime_ms)
{
    check_period(m, uptime_ms);
    if (sgm_store_should_commit(&m->policy, m->unsaved_pulses, uptime_ms - m->last_save_uptime_ms)) {
        save(m, uptime_ms);
    }
}

void sgm_meter_snapshot(sgm_meter_t *m, uint64_t uptime_ms)
{
    check_period(m, uptime_ms);
    int64_t now = 0;
    sgm_meter_now(m, uptime_ms, &now);
    enqueue(m, SGM_REC_INTERVAL, 0, now, uptime_ms, NULL);
}

void sgm_meter_event(sgm_meter_t *m, uint16_t events, uint64_t uptime_ms)
{
    check_period(m, uptime_ms);
    int64_t now = 0;
    sgm_meter_now(m, uptime_ms, &now);
    enqueue(m, SGM_REC_EVENT, events, now, uptime_ms, NULL);
}

void sgm_meter_flush(sgm_meter_t *m, uint64_t uptime_ms)
{
    if (m->unsaved_pulses) {
        save(m, uptime_ms);
    }
}

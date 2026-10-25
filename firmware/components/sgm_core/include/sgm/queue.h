/*
 * Bounded store-and-forward queue for telemetry records.
 *
 * When full, the oldest *interval* record is dropped first: interval records
 * are redundant (the next one carries the same cumulative counter), while a
 * period-close record is the billing reading itself and is kept as long as
 * any interval record can be sacrificed instead.
 */
#ifndef SGM_QUEUE_H
#define SGM_QUEUE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "sgm/record.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    sgm_record_t *buf;
    uint16_t cap;
    uint16_t head; /* index of the oldest record */
    uint16_t count;
    uint32_t dropped;
} sgm_queue_t;

void sgm_queue_init(sgm_queue_t *q, sgm_record_t *storage, uint16_t capacity);
/* Returns true if stored without loss, false if an older record was dropped. */
bool sgm_queue_push(sgm_queue_t *q, const sgm_record_t *rec);
/* i = 0 is the oldest record. NULL when out of range. */
sgm_record_t *sgm_queue_at(sgm_queue_t *q, uint16_t i);
/* Remove the n oldest records (after the backend acknowledged them). */
void sgm_queue_pop(sgm_queue_t *q, uint16_t n);
/* Remove every leading record with sequence <= last_sequence. Safer than
 * pop(n) when the queue may have been trimmed while a batch was in flight. */
uint16_t sgm_queue_ack(sgm_queue_t *q, uint32_t last_sequence);
static inline uint16_t sgm_queue_count(const sgm_queue_t *q) { return q->count; }

#ifdef __cplusplus
}
#endif
#endif

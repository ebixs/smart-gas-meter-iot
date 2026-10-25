#include "sgm/queue.h"

void sgm_queue_init(sgm_queue_t *q, sgm_record_t *storage, uint16_t capacity)
{
    q->buf = storage;
    q->cap = capacity;
    q->head = 0;
    q->count = 0;
    q->dropped = 0;
}

static uint16_t slot(const sgm_queue_t *q, uint16_t i)
{
    return (uint16_t)((q->head + i) % q->cap);
}

sgm_record_t *sgm_queue_at(sgm_queue_t *q, uint16_t i)
{
    return i < q->count ? &q->buf[slot(q, i)] : NULL;
}

/* Remove logical element i, keeping the order of the rest. */
static void remove_at(sgm_queue_t *q, uint16_t i)
{
    for (uint16_t k = i; k > 0; k--) {
        q->buf[slot(q, k)] = q->buf[slot(q, (uint16_t)(k - 1))];
    }
    q->head = slot(q, 1);
    q->count--;
}

bool sgm_queue_push(sgm_queue_t *q, const sgm_record_t *rec)
{
    bool lossless = true;
    if (q->count == q->cap) {
        uint16_t victim = 0;
        for (uint16_t i = 0; i < q->count; i++) {
            if (q->buf[slot(q, i)].type == SGM_REC_INTERVAL) {
                victim = i;
                break;
            }
        }
        remove_at(q, victim);
        q->dropped++;
        lossless = false;
    }
    q->buf[slot(q, q->count)] = *rec;
    q->count++;
    return lossless;
}

void sgm_queue_pop(sgm_queue_t *q, uint16_t n)
{
    if (n > q->count) {
        n = q->count;
    }
    q->head = slot(q, n);
    q->count = (uint16_t)(q->count - n);
}

uint16_t sgm_queue_ack(sgm_queue_t *q, uint32_t last_sequence)
{
    uint16_t n = 0;
    while (q->count && q->buf[q->head].sequence <= last_sequence) {
        sgm_queue_pop(q, 1);
        n++;
    }
    return n;
}

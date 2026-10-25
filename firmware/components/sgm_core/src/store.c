#include "sgm/store.h"

#include <string.h>

uint32_t sgm_crc32(const uint8_t *data, size_t len)
{
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int b = 0; b < 8; b++) {
            crc = (crc >> 1) ^ (0xEDB88320u & (uint32_t)(-(int32_t)(crc & 1u)));
        }
    }
    return ~crc;
}

static void put_u16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void put_u32(uint8_t *p, uint32_t v) { for (int i = 0; i < 4; i++) p[i] = (uint8_t)(v >> (8 * i)); }
static void put_u64(uint8_t *p, uint64_t v) { for (int i = 0; i < 8; i++) p[i] = (uint8_t)(v >> (8 * i)); }
static uint16_t get_u16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static uint32_t get_u32(const uint8_t *p)
{
    uint32_t v = 0;
    for (int i = 3; i >= 0; i--) v = (v << 8) | p[i];
    return v;
}
static uint64_t get_u64(const uint8_t *p)
{
    uint64_t v = 0;
    for (int i = 7; i >= 0; i--) v = (v << 8) | p[i];
    return v;
}

/* Layout: magic u32 | version u16 | period_year i16 | period_month u8 | period_months u8 |
 * reserved u16 | generation u32 | sequence u32 | pulse_total u64 | boot_count u32 |
 * reserved u32 | crc32 u32  = 40 bytes */
void sgm_store_encode(const sgm_persist_t *st, uint8_t out[SGM_STORE_IMAGE_LEN])
{
    memset(out, 0, SGM_STORE_IMAGE_LEN);
    put_u32(out + 0, SGM_STORE_MAGIC);
    put_u16(out + 4, SGM_STORE_VERSION);
    put_u16(out + 6, (uint16_t)st->open_period.year);
    out[8] = (uint8_t)st->open_period.month;
    out[9] = (uint8_t)st->open_period.months;
    put_u32(out + 12, st->generation);
    put_u32(out + 16, st->sequence);
    put_u64(out + 20, st->pulse_total);
    put_u32(out + 28, st->boot_count);
    put_u32(out + 36, sgm_crc32(out, 36));
}

int sgm_store_decode(const uint8_t in[SGM_STORE_IMAGE_LEN], sgm_persist_t *st)
{
    if (get_u32(in) != SGM_STORE_MAGIC || get_u16(in + 4) != SGM_STORE_VERSION) {
        return -1;
    }
    if (get_u32(in + 36) != sgm_crc32(in, 36)) {
        return -1;
    }
    st->open_period.year = (int16_t)get_u16(in + 6);
    st->open_period.month = (int8_t)in[8];
    st->open_period.months = (int8_t)in[9];
    st->generation = get_u32(in + 12);
    st->sequence = get_u32(in + 16);
    st->pulse_total = get_u64(in + 20);
    st->boot_count = get_u32(in + 28);
    return 0;
}

static int read_slot(const sgm_store_io_t *io, int slot, sgm_persist_t *st)
{
    uint8_t buf[SGM_STORE_IMAGE_LEN];
    if (io->read(io->ctx, slot, buf, sizeof buf) != 0) {
        return -1;
    }
    return sgm_store_decode(buf, st);
}

int sgm_store_load(const sgm_store_io_t *io, sgm_persist_t *out)
{
    sgm_persist_t a, b;
    int va = read_slot(io, 0, &a) == 0;
    int vb = read_slot(io, 1, &b) == 0;
    if (!va && !vb) {
        memset(out, 0, sizeof(*out));
        return SGM_STORE_EMPTY;
    }
    /* Generation wraps after 2^32 saves; compare with serial-number arithmetic. */
    if (va && vb) {
        *out = ((int32_t)(a.generation - b.generation) >= 0) ? a : b;
    } else {
        *out = va ? a : b;
    }
    return SGM_STORE_OK;
}

int sgm_store_save(const sgm_store_io_t *io, sgm_persist_t *st)
{
    st->generation++;
    uint8_t buf[SGM_STORE_IMAGE_LEN];
    sgm_store_encode(st, buf);
    return io->write(io->ctx, (int)(st->generation & 1u), buf, sizeof buf) == 0 ? SGM_STORE_OK : SGM_STORE_IO_ERROR;
}

int sgm_store_should_commit(const sgm_commit_policy_t *p, uint64_t unsaved_pulses, uint64_t ms_since_save)
{
    if (unsaved_pulses == 0) {
        return 0;
    }
    return unsaved_pulses >= p->every_pulses || ms_since_save >= p->max_age_ms;
}

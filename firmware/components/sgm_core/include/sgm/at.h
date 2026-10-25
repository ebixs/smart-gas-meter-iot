/*
 * Line-oriented parser for 3GPP / Quectel AT responses.
 *
 * The modem driver feeds UART bytes into sgm_at_linebuf and classifies each
 * complete line. Only the responses the uplink needs are decoded; anything
 * else is reported as SGM_AT_OTHER so URCs never stall a command.
 */
#ifndef SGM_AT_H
#define SGM_AT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    SGM_AT_OTHER = 0,
    SGM_AT_OK,
    SGM_AT_ERROR,
    SGM_AT_CME_ERROR,    /* a = error code */
    SGM_AT_CSQ,          /* a = rssi index 0..31/99, b = ber */
    SGM_AT_REG,          /* +CREG/+CGREG/+CEREG: a = stat, b = 1 when registered (home or roaming) */
    SGM_AT_CCLK,         /* unix_s = network time converted to UTC */
    SGM_AT_HTTP_RESULT,  /* +QHTTPPOST/+QHTTPGET: a = module error (0 ok), b = HTTP status */
    SGM_AT_CONNECT,      /* data prompt before an HTTP body */
    SGM_AT_SMS_PROMPT,   /* "> " before an SMS body */
    SGM_AT_CMGS,         /* a = SMS message reference */
} sgm_at_kind_t;

typedef struct {
    sgm_at_kind_t kind;
    int a;
    int b;
    int64_t unix_s;
} sgm_at_result_t;

sgm_at_kind_t sgm_at_parse_line(const char *line, sgm_at_result_t *out);

/* rssi index from +CSQ (0..31, 99 = unknown) to dBm; INT16_MIN when unknown. */
int sgm_csq_to_dbm(int rssi_index);

typedef struct {
    char buf[256];
    size_t len;
    bool overflow;
} sgm_at_linebuf_t;

void sgm_at_linebuf_init(sgm_at_linebuf_t *lb);
/* Feed one byte. Returns true when a complete non-empty line is in lb->buf
 * (NUL-terminated, without CR/LF). The SMS prompt "> " counts as a line. */
bool sgm_at_linebuf_feed(sgm_at_linebuf_t *lb, char c);

#ifdef __cplusplus
}
#endif
#endif

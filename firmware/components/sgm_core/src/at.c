#include "sgm/at.h"

#include <stdio.h>
#include <string.h>

#include "sgm/jalali.h"
#include "sgm/record.h"

static bool starts(const char *s, const char *prefix) { return strncmp(s, prefix, strlen(prefix)) == 0; }

/* "+CCLK: \"yy/MM/dd,hh:mm:ss±zz\"" where zz is the local offset in quarter hours. */
static bool parse_cclk(const char *s, int64_t *unix_s)
{
    int yy, mo, dd, hh, mi, ss, tz;
    char sign;
    if (sscanf(s, "+CCLK: \"%d/%d/%d,%d:%d:%d%c%d\"", &yy, &mo, &dd, &hh, &mi, &ss, &sign, &tz) != 8) {
        return false;
    }
    if (sign != '+' && sign != '-') {
        return false;
    }
    if (mo < 1 || mo > 12 || dd < 1 || dd > 31 || hh > 23 || mi > 59 || ss > 60 || yy < 0 || yy > 99) {
        return false;
    }
    int64_t local = (int64_t)sgm_days_from_gregorian(2000 + yy, mo, dd) * 86400 + hh * 3600 + mi * 60 + ss;
    int64_t offset = (int64_t)tz * 15 * 60 * (sign == '-' ? -1 : 1);
    *unix_s = local - offset;
    return true;
}

sgm_at_kind_t sgm_at_parse_line(const char *line, sgm_at_result_t *out)
{
    memset(out, 0, sizeof(*out));
    int a = 0, b = 0, c = 0;
    if (strcmp(line, "OK") == 0) {
        out->kind = SGM_AT_OK;
    } else if (strcmp(line, "ERROR") == 0) {
        out->kind = SGM_AT_ERROR;
    } else if (sscanf(line, "+CME ERROR: %d", &a) == 1 || sscanf(line, "+CMS ERROR: %d", &a) == 1) {
        out->kind = SGM_AT_CME_ERROR;
        out->a = a;
    } else if (sscanf(line, "+CSQ: %d,%d", &a, &b) == 2) {
        out->kind = SGM_AT_CSQ;
        out->a = a;
        out->b = b;
    } else if (starts(line, "+CREG:") || starts(line, "+CGREG:") || starts(line, "+CEREG:")) {
        /* Solicited reply "n,stat[,\"lac\",...]"; URC "stat[,\"lac\",...]". The second
         * token is a bare number only in the solicited form. */
        const char *p = strchr(line, ':') + 1;
        if (sscanf(p, " %d", &a) != 1) {
            return out->kind;
        }
        const char *comma = strchr(p, ',');
        int stat = a;
        if (comma && comma[1] != '"' && sscanf(comma + 1, "%d", &b) == 1) {
            stat = b;
        }
        out->kind = SGM_AT_REG;
        out->a = stat;
        out->b = (stat == 1 || stat == 5);
    } else if (starts(line, "+CCLK:")) {
        if (parse_cclk(line, &out->unix_s)) {
            out->kind = SGM_AT_CCLK;
        }
    } else if (sscanf(line, "+QHTTPPOST: %d,%d", &a, &b) >= 1 || sscanf(line, "+QHTTPGET: %d,%d", &a, &b) >= 1) {
        out->kind = SGM_AT_HTTP_RESULT;
        out->a = a;
        out->b = b;
    } else if (starts(line, "CONNECT")) {
        out->kind = SGM_AT_CONNECT;
    } else if (strcmp(line, ">") == 0 || strcmp(line, "> ") == 0) {
        out->kind = SGM_AT_SMS_PROMPT;
    } else if (sscanf(line, "+CMGS: %d", &c) == 1) {
        out->kind = SGM_AT_CMGS;
        out->a = c;
    }
    return out->kind;
}

int sgm_csq_to_dbm(int rssi_index)
{
    if (rssi_index < 0 || rssi_index > 31) {
        return SGM_RSSI_UNKNOWN;
    }
    return -113 + 2 * rssi_index;
}

void sgm_at_linebuf_init(sgm_at_linebuf_t *lb)
{
    lb->len = 0;
    lb->overflow = false;
    lb->buf[0] = '\0';
}

bool sgm_at_linebuf_feed(sgm_at_linebuf_t *lb, char c)
{
    if (c == '\r' || c == '\n') {
        bool complete = lb->len > 0 && !lb->overflow;
        lb->buf[lb->len] = '\0';
        if (!complete) {
            lb->len = 0;
            lb->overflow = false;
            return false;
        }
        lb->len = 0;
        return true;
    }
    if (lb->len + 1 >= sizeof lb->buf) {
        lb->overflow = true; /* drop the rest of an over-long line */
        return false;
    }
    lb->buf[lb->len++] = c;
    lb->buf[lb->len] = '\0';
    /* The SMS prompt is not newline-terminated. */
    if (lb->len == 2 && lb->buf[0] == '>' && lb->buf[1] == ' ') {
        lb->len = 0;
        return true;
    }
    return false;
}

/*
 * SMS fallback for the billing reading.
 *
 * When the data uplink cannot deliver a period-close record, the device sends
 * one plain GSM-7 text that the operator's SMS gateway can parse, and that a
 * subscriber can read on a phone:
 *
 *   SGM1 sgm-0001 P=1404/07x3 C=123456 S=812 T=20260922T2030Z
 *
 * P = Jalali period start / length in months, C = cumulative pulse count at
 * the boundary, S = telemetry sequence, T = boundary time (UTC). The record
 * stays queued until the data uplink acknowledges it; the SMS is a duplicate
 * channel, never a replacement, and carries no price.
 */
#ifndef SGM_SMS_H
#define SGM_SMS_H

#include <stddef.h>

#include "sgm/record.h"
#include "sgm/telemetry.h"

#ifdef __cplusplus
extern "C" {
#endif

#define SGM_SMS_MAX 160

/* Returns text length (<= 160) or a negative SGM_JSON_* error. */
int sgm_sms_period_close(const sgm_record_t *rec, const sgm_device_info_t *dev, char *out, size_t n);

#ifdef __cplusplus
}
#endif
#endif

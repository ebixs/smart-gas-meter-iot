/* Transport behind the store-and-forward queue: Wi-Fi (bench) or cellular. */
#ifndef SGM_UPLINK_H
#define SGM_UPLINK_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

typedef struct {
    const char *name;
    /* Bring the link up (blocking, bounded). */
    esp_err_t (*connect)(void);
    /* POST a JSON body; *http_status receives the HTTP status code. */
    esp_err_t (*post_json)(const char *body, size_t len, int *http_status);
    /* Wall clock if the link knows it; *source is an sgm_time_source_t. */
    bool (*get_time)(int64_t *unix_ms, uint8_t *source);
    /* Signal strength in dBm or INT16_MIN. */
    int16_t (*rssi_dbm)(void);
    /* Plain-text SMS; ESP_ERR_NOT_SUPPORTED on Wi-Fi. */
    esp_err_t (*send_sms)(const char *number, const char *text);
    /* Power down radio between uploads. */
    void (*disconnect)(void);
} sgm_uplink_t;

const sgm_uplink_t *sgm_uplink_wifi(void);
const sgm_uplink_t *sgm_uplink_cell(void);

#endif

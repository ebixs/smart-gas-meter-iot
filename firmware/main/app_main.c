/*
 * Smart Gas Meter bench firmware (ESP32-S3).
 *
 * Bench use only: J2 takes a synthetic 3.3 V pulse or a dry contact to GND.
 * Never connect a live gas meter, gas line, valve, mains or field wiring.
 *
 * Tasks
 *   pulse  (prio 10): GPIO edges -> debounce -> meter counter (+ flash commit)
 *   report (prio 5) : tamper input, interval snapshots, store-and-forward uplink
 */
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "board.h"
#include "driver/gpio.h"
#include "esp_app_desc.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_random.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "nvs_store.h"
#include "sdkconfig.h"
#include "sgm/backoff.h"
#include "sgm/debounce.h"
#include "sgm/meter.h"
#include "sgm/sms.h"
#include "sgm/telemetry.h"
#include "uplink.h"

static const char *TAG = "sgm";

#define BATCH_MAX 16
#define SMS_FALLBACK_AFTER_MS (24ULL * 3600 * 1000)

typedef struct {
    int level;
    int64_t t_us;
} edge_t;

static QueueHandle_t s_edges;
static SemaphoreHandle_t s_lock;
static sgm_meter_t s_meter;
static sgm_record_t s_queue_storage[CONFIG_SGM_QUEUE_LEN];
static sgm_queue_t s_queue;
static sgm_device_info_t s_dev;
static char s_device_id[32];
static const sgm_uplink_t *s_uplink;

static uint64_t uptime_ms(void) { return (uint64_t)(esp_timer_get_time() / 1000); }

static void pulse_isr(void *arg)
{
    (void)arg;
    edge_t e = {gpio_get_level(SGM_GPIO_PULSE_IN), esp_timer_get_time()};
    BaseType_t woken = pdFALSE;
    xQueueSendFromISR(s_edges, &e, &woken); /* a full queue drops edges: bursts are bounce anyway */
    if (woken) {
        portYIELD_FROM_ISR();
    }
}

static void led_blink(int ms)
{
    gpio_set_level(SGM_GPIO_LED, 1);
    vTaskDelay(pdMS_TO_TICKS(ms));
    gpio_set_level(SGM_GPIO_LED, 0);
}

static void pulse_task(void *arg)
{
    (void)arg;
    sgm_debounce_cfg_t cfg = {
        .min_low_us = CONFIG_SGM_DEBOUNCE_MIN_LOW_MS * 1000u,
        .min_high_us = CONFIG_SGM_DEBOUNCE_MIN_HIGH_MS * 1000u,
        .min_period_us = CONFIG_SGM_MIN_PULSE_PERIOD_MS * 1000u,
    };
    sgm_debounce_t deb;
    sgm_debounce_init(&deb, &cfg, gpio_get_level(SGM_GPIO_PULSE_IN), esp_timer_get_time());
    edge_t e;
    for (;;) {
        if (xQueueReceive(s_edges, &e, pdMS_TO_TICKS(1000)) == pdTRUE) {
            int q = sgm_debounce_edge(&deb, e.level, e.t_us);
            if (q) {
                xSemaphoreTake(s_lock, portMAX_DELAY);
                sgm_meter_pulse(&s_meter, (uint64_t)(e.t_us / 1000), q == 2);
                uint64_t total = s_meter.st.pulse_total;
                xSemaphoreGive(s_lock);
                ESP_LOGI(TAG, "pulse %" PRIu64 "%s", total, q == 2 ? " (faster than Qmax)" : "");
                led_blink(20);
            }
        }
        xSemaphoreTake(s_lock, portMAX_DELAY);
        sgm_meter_tick(&s_meter, uptime_ms());
        xSemaphoreGive(s_lock);
    }
}

/* Copy up to BATCH_MAX synced records out of the queue (the queue may change while we send). */
static size_t take_batch(sgm_record_t *out)
{
    size_t n = 0;
    xSemaphoreTake(s_lock, portMAX_DELAY);
    for (uint16_t i = 0; i < sgm_queue_count(&s_queue) && n < BATCH_MAX; i++) {
        sgm_record_t *r = sgm_queue_at(&s_queue, i);
        if (r->time_source == SGM_TIME_UNSYNCED) {
            break; /* keep order: wait for the clock */
        }
        out[n++] = *r;
    }
    xSemaphoreGive(s_lock);
    return n;
}

static void sms_fallback(void)
{
#if CONFIG_SGM_UPLINK_CELL
    if (strlen(CONFIG_SGM_SMS_GATEWAY) == 0) {
        return;
    }
    xSemaphoreTake(s_lock, portMAX_DELAY);
    for (uint16_t i = 0; i < sgm_queue_count(&s_queue); i++) {
        sgm_record_t *r = sgm_queue_at(&s_queue, i);
        if (r->type != SGM_REC_PERIOD_CLOSE || (r->flags & SGM_RECF_SMS_SENT) ||
            uptime_ms() - r->uptime_ms < SMS_FALLBACK_AFTER_MS) {
            continue;
        }
        char text[SGM_SMS_MAX + 1];
        if (sgm_sms_period_close(r, &s_dev, text, sizeof text) > 0) {
            r->flags |= SGM_RECF_SMS_SENT; /* one attempt per record; the queue still holds it */
            xSemaphoreGive(s_lock);
            esp_err_t err = s_uplink->send_sms(CONFIG_SGM_SMS_GATEWAY, text);
            ESP_LOGW(TAG, "period-close SMS fallback: %s", esp_err_to_name(err));
            return;
        }
    }
    xSemaphoreGive(s_lock);
#endif
}

/* One upload cycle. Returns true when the queue was drained (or only unsynced records remain). */
static bool upload_cycle(void)
{
    if (!s_uplink) {
        return false;
    }
    esp_err_t err = s_uplink->connect();
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "%s connect failed: %s", s_uplink->name, esp_err_to_name(err));
        sms_fallback();
        return false;
    }
    int64_t unix_ms;
    uint8_t source;
    if (s_uplink->get_time(&unix_ms, &source)) {
        xSemaphoreTake(s_lock, portMAX_DELAY);
        sgm_meter_set_time(&s_meter, unix_ms, uptime_ms(), source);
        s_meter.rssi_dbm = s_uplink->rssi_dbm();
        xSemaphoreGive(s_lock);
    }

    static sgm_record_t batch[BATCH_MAX];
    static char body[BATCH_MAX * 420];
    bool drained = false;
    for (int round = 0; round < 32; round++) {
        size_t n = take_batch(batch);
        if (n == 0) {
            drained = true;
            break;
        }
        const sgm_record_t *ptrs[BATCH_MAX];
        for (size_t i = 0; i < n; i++) {
            ptrs[i] = &batch[i];
        }
        size_t encoded = 0;
        int len = sgm_telemetry_batch_json(ptrs, n, &s_dev, body, sizeof body, &encoded);
        if (len < 0 || encoded == 0) {
            ESP_LOGE(TAG, "cannot encode batch (%d)", len);
            break;
        }
        int status = 0;
        err = s_uplink->post_json(body, (size_t)len, &status);
        if (err != ESP_OK || status == 0 || status >= 500 || status == 401 || status == 429) {
            ESP_LOGW(TAG, "upload failed: %s, HTTP %d", esp_err_to_name(err), status);
            sms_fallback();
            break;
        }
        /* 2xx: stored. Other 4xx: the backend rejected the records for good (it logs
         * them); acknowledge so one bad record cannot block the queue forever. */
        if (status >= 400) {
            ESP_LOGE(TAG, "backend rejected batch with HTTP %d; dropping %u records", status, (unsigned)encoded);
        }
        xSemaphoreTake(s_lock, portMAX_DELAY);
        sgm_queue_ack(&s_queue, batch[encoded - 1].sequence);
        xSemaphoreGive(s_lock);
    }
    s_uplink->disconnect();
    return drained;
}

static void report_task(void *arg)
{
    (void)arg;
    sgm_backoff_t backoff;
    sgm_backoff_init(&backoff, 30000, 3600000, esp_random());
    uint64_t next_snapshot = uptime_ms() + CONFIG_SGM_SNAPSHOT_INTERVAL_S * 1000ULL;
    uint64_t next_upload = uptime_ms() + 5000; /* first contact soon after boot: get the clock */
    int tamper = gpio_get_level(SGM_GPIO_TAMPER_IN), tamper_same = 0, tamper_candidate = tamper;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(200));
        uint64_t now = uptime_ms();

        /* Tamper: hardware RC + 3 equal samples (600 ms) before an event. Advisory only. */
        int level = gpio_get_level(SGM_GPIO_TAMPER_IN);
        tamper_same = (level == tamper_candidate) ? tamper_same + 1 : 0;
        tamper_candidate = level;
        if (tamper_same >= 3 && level != tamper) {
            tamper = level;
            xSemaphoreTake(s_lock, portMAX_DELAY);
            sgm_meter_event(&s_meter, level ? SGM_EVT_TAMPER_OPEN : SGM_EVT_TAMPER_CLOSED, now);
            xSemaphoreGive(s_lock);
            ESP_LOGW(TAG, "tamper input %s", level ? "OPEN" : "closed");
            next_upload = now; /* report promptly */
        }

        if (now >= next_snapshot) {
            xSemaphoreTake(s_lock, portMAX_DELAY);
            sgm_meter_snapshot(&s_meter, now);
            xSemaphoreGive(s_lock);
            next_snapshot += CONFIG_SGM_SNAPSHOT_INTERVAL_S * 1000ULL;
        }

        if (now >= next_upload) {
            if (upload_cycle()) {
                sgm_backoff_reset(&backoff);
                next_upload = uptime_ms() + CONFIG_SGM_UPLINK_INTERVAL_S * 1000ULL;
            } else {
                uint32_t wait = sgm_backoff_next(&backoff);
                ESP_LOGI(TAG, "retry upload in %" PRIu32 " s", wait / 1000);
                next_upload = uptime_ms() + wait;
            }
        }
    }
}

static uint16_t reset_events(void)
{
    switch (esp_reset_reason()) {
    case ESP_RST_BROWNOUT: return SGM_EVT_BROWNOUT_RESET;
    case ESP_RST_TASK_WDT:
    case ESP_RST_INT_WDT:
    case ESP_RST_WDT: return SGM_EVT_WATCHDOG_RESET;
    default: return 0;
    }
}

void app_main(void)
{
    const esp_app_desc_t *app = esp_app_get_description();
    if (strlen(CONFIG_SGM_DEVICE_ID) > 0) {
        strlcpy(s_device_id, CONFIG_SGM_DEVICE_ID, sizeof s_device_id);
    } else {
        uint8_t mac[6];
        esp_read_mac(mac, ESP_MAC_WIFI_STA);
        snprintf(s_device_id, sizeof s_device_id, "sgm-%02x%02x%02x", mac[3], mac[4], mac[5]);
    }
    s_dev.device_id = s_device_id;
    s_dev.fw_version = app->version;
    s_dev.input_mode = CONFIG_SGM_INPUT_MODE;
    ESP_LOGI(TAG, "%s firmware %s, bench use only (synthetic 3.3 V pulses)", s_device_id, app->version);

    gpio_config_t led = {.pin_bit_mask = 1ULL << SGM_GPIO_LED, .mode = GPIO_MODE_OUTPUT};
    gpio_config(&led);
    gpio_config_t tamper = {.pin_bit_mask = 1ULL << SGM_GPIO_TAMPER_IN, .mode = GPIO_MODE_INPUT};
    gpio_config(&tamper);

    s_lock = xSemaphoreCreateMutex();
    sgm_queue_init(&s_queue, s_queue_storage, CONFIG_SGM_QUEUE_LEN);
    sgm_meter_cfg_t cfg = {
        .policy = {.every_pulses = CONFIG_SGM_COMMIT_EVERY_PULSES, .max_age_ms = 15 * 60 * 1000},
        .queue = &s_queue,
#if CONFIG_SGM_PERIOD_MONTHLY
        .period_months = 1,
#else
        .period_months = 3,
#endif
        .tz_offset_s = SGM_TZ_IRAN_S,
        .boot_events = reset_events(),
    };
    ESP_ERROR_CHECK(sgm_nvs_store_init(&cfg.io));
    sgm_meter_boot(&s_meter, &cfg, uptime_ms());
    ESP_LOGI(TAG, "counter %" PRIu64 " pulses, boot #%" PRIu32, s_meter.st.pulse_total, s_meter.st.boot_count);

#if CONFIG_SGM_UPLINK_CELL
    s_uplink = sgm_uplink_cell();
#else
    s_uplink = sgm_uplink_wifi();
#endif

    s_edges = xQueueCreate(64, sizeof(edge_t));
    gpio_config_t pulse = {
        .pin_bit_mask = 1ULL << SGM_GPIO_PULSE_IN,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE, /* R5 10k on the board */
        .intr_type = GPIO_INTR_ANYEDGE,
    };
    ESP_ERROR_CHECK(gpio_config(&pulse));
    ESP_ERROR_CHECK(gpio_install_isr_service(0));
    ESP_ERROR_CHECK(gpio_isr_handler_add(SGM_GPIO_PULSE_IN, pulse_isr, NULL));

    xTaskCreate(pulse_task, "pulse", 4096, NULL, 10, NULL);
    xTaskCreate(report_task, "report", 8192, NULL, 5, NULL);
}

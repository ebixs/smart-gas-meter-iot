/* Bench uplink: Wi-Fi station + SNTP + HTTP(S) POST to the lab backend. */
#include <string.h>
#include <sys/time.h>

#include "esp_crt_bundle.h"
#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_netif_sntp.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "sdkconfig.h"
#include "sgm/record.h"
#include "uplink.h"

#if CONFIG_SGM_UPLINK_WIFI

static const char *TAG = "uplink_wifi";
static EventGroupHandle_t s_events;
static bool s_started, s_sntp_started;
#define BIT_CONNECTED BIT0

static void on_wifi_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    (void)arg;
    (void)data;
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(s_events, BIT_CONNECTED);
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(s_events, BIT_CONNECTED);
    }
}

static esp_err_t wifi_connect(void)
{
    if (!s_started) {
        if (strlen(CONFIG_SGM_WIFI_SSID) == 0) {
            ESP_LOGE(TAG, "Wi-Fi SSID not configured (idf.py menuconfig -> Smart Gas Meter)");
            return ESP_ERR_INVALID_STATE;
        }
        s_events = xEventGroupCreate();
        ESP_ERROR_CHECK(esp_netif_init());
        ESP_ERROR_CHECK(esp_event_loop_create_default());
        esp_netif_create_default_wifi_sta();
        wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
        ESP_ERROR_CHECK(esp_wifi_init(&init));
        ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_DISCONNECTED, on_wifi_event, NULL));
        ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, on_wifi_event, NULL));
        wifi_config_t cfg = {0};
        strlcpy((char *)cfg.sta.ssid, CONFIG_SGM_WIFI_SSID, sizeof cfg.sta.ssid);
        strlcpy((char *)cfg.sta.password, CONFIG_SGM_WIFI_PASSWORD, sizeof cfg.sta.password);
        ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
        ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &cfg));
        ESP_ERROR_CHECK(esp_wifi_start());
        esp_wifi_connect();
        s_started = true;
    }
    EventBits_t bits = xEventGroupWaitBits(s_events, BIT_CONNECTED, pdFALSE, pdTRUE, pdMS_TO_TICKS(20000));
    if (!(bits & BIT_CONNECTED)) {
        return ESP_ERR_TIMEOUT;
    }
    if (!s_sntp_started) {
        esp_sntp_config_t sntp = ESP_NETIF_SNTP_DEFAULT_CONFIG("pool.ntp.org");
        esp_netif_sntp_init(&sntp);
        s_sntp_started = true;
    }
    return ESP_OK;
}

static esp_err_t wifi_post(const char *body, size_t len, int *http_status)
{
    esp_http_client_config_t cfg = {
        .url = CONFIG_SGM_API_URL,
        .method = HTTP_METHOD_POST,
        .timeout_ms = 15000,
        .crt_bundle_attach = esp_crt_bundle_attach,
    };
    esp_http_client_handle_t c = esp_http_client_init(&cfg);
    if (!c) {
        return ESP_ERR_NO_MEM;
    }
    char auth[160];
    snprintf(auth, sizeof auth, "Bearer %s", CONFIG_SGM_API_TOKEN);
    esp_http_client_set_header(c, "Content-Type", "application/json");
    esp_http_client_set_header(c, "Authorization", auth);
    esp_http_client_set_post_field(c, body, (int)len);
    esp_err_t err = esp_http_client_perform(c);
    *http_status = err == ESP_OK ? esp_http_client_get_status_code(c) : 0;
    esp_http_client_cleanup(c);
    return err;
}

static bool wifi_time(int64_t *unix_ms, uint8_t *source)
{
    if (!s_sntp_started || esp_netif_sntp_sync_wait(pdMS_TO_TICKS(10000)) != ESP_OK) {
        return false;
    }
    struct timeval tv;
    gettimeofday(&tv, NULL);
    if (tv.tv_sec < 1700000000) { /* not set yet */
        return false;
    }
    *unix_ms = (int64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000;
    *source = SGM_TIME_SNTP;
    return true;
}

static int16_t wifi_rssi(void)
{
    wifi_ap_record_t ap;
    return esp_wifi_sta_get_ap_info(&ap) == ESP_OK ? ap.rssi : SGM_RSSI_UNKNOWN;
}

static esp_err_t wifi_sms(const char *number, const char *text)
{
    (void)number;
    (void)text;
    return ESP_ERR_NOT_SUPPORTED;
}

static void wifi_disconnect(void) { /* stay associated on the bench */ }

static const sgm_uplink_t WIFI = {"wifi", wifi_connect, wifi_post, wifi_time, wifi_rssi, wifi_sms, wifi_disconnect};

const sgm_uplink_t *sgm_uplink_wifi(void) { return &WIFI; }

#else
const sgm_uplink_t *sgm_uplink_wifi(void) { return NULL; }
#endif

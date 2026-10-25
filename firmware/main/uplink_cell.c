/*
 * Cellular uplink over the J6 modem daughterboard (UART1, 3.3 V logic).
 *
 * Written against the Quectel AT command set shared by BG95/BG77 (LTE-M/NB-IoT)
 * and EC200U/EG915U (LTE Cat-1): AT+QICSGP/QIACT for the PDP context,
 * AT+QHTTPURL/QHTTPPOST for HTTP and AT+CMGS for the SMS fallback.
 * Not yet exercised on hardware: the daughterboard is a v0.3 decision
 * (docs/hardware-decisions.md). Plain HTTP only; TLS needs a CA loaded into
 * the modem (AT+QSSLCFG) and is listed as a follow-up.
 */
#include <stdio.h>
#include <string.h>

#include "board.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include "sgm/at.h"
#include "sgm/record.h"
#include "uplink.h"

#if CONFIG_SGM_UPLINK_CELL

static const char *TAG = "uplink_cell";
static sgm_at_linebuf_t s_lb;
static bool s_uart_ready, s_powered;
static int16_t s_rssi = SGM_RSSI_UNKNOWN;

static int64_t now_ms(void) { return esp_timer_get_time() / 1000; }

static void uart_setup(void)
{
    if (s_uart_ready) {
        return;
    }
    uart_config_t cfg = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    ESP_ERROR_CHECK(uart_driver_install(SGM_MODEM_UART, 2048, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(SGM_MODEM_UART, &cfg));
    ESP_ERROR_CHECK(uart_set_pin(SGM_MODEM_UART, SGM_GPIO_MODEM_TXD, SGM_GPIO_MODEM_RXD, UART_PIN_NO_CHANGE,
                                 UART_PIN_NO_CHANGE));
    gpio_config_t out = {.pin_bit_mask = (1ULL << SGM_GPIO_MODEM_EN) | (1ULL << SGM_GPIO_MODEM_RESET),
                         .mode = GPIO_MODE_OUTPUT};
    gpio_config(&out);
    gpio_set_level(SGM_GPIO_MODEM_RESET, 0);
    gpio_config_t in = {.pin_bit_mask = 1ULL << SGM_GPIO_MODEM_STATUS, .mode = GPIO_MODE_INPUT};
    gpio_config(&in);
    sgm_at_linebuf_init(&s_lb);
    s_uart_ready = true;
}

/* Read lines until one of kind `until` (or OK/ERROR when until == SGM_AT_OK) or timeout.
 * `capture` (optional) receives the last line of kind `capture_kind`. */
static sgm_at_kind_t wait_for(sgm_at_kind_t until, int timeout_ms, sgm_at_kind_t capture_kind,
                              sgm_at_result_t *capture)
{
    int64_t deadline = now_ms() + timeout_ms;
    uint8_t c;
    while (now_ms() < deadline) {
        if (uart_read_bytes(SGM_MODEM_UART, &c, 1, pdMS_TO_TICKS(50)) != 1) {
            continue;
        }
        if (!sgm_at_linebuf_feed(&s_lb, (char)c)) {
            continue;
        }
        sgm_at_result_t r;
        sgm_at_kind_t k = sgm_at_parse_line(s_lb.buf, &r);
        if (k == SGM_AT_CSQ) {
            s_rssi = (int16_t)sgm_csq_to_dbm(r.a);
        }
        if (capture && k == capture_kind && k != SGM_AT_OTHER) {
            *capture = r;
        }
        if (k == until) {
            return k;
        }
        if (k == SGM_AT_ERROR || k == SGM_AT_CME_ERROR) {
            ESP_LOGW(TAG, "modem: %s", s_lb.buf);
            return k;
        }
    }
    return SGM_AT_OTHER; /* timeout */
}

static void send_raw(const char *s, size_t n) { uart_write_bytes(SGM_MODEM_UART, s, n); }

static bool at(const char *cmd, int timeout_ms)
{
    uart_flush_input(SGM_MODEM_UART);
    send_raw(cmd, strlen(cmd));
    send_raw("\r", 1);
    return wait_for(SGM_AT_OK, timeout_ms, SGM_AT_OTHER, NULL) == SGM_AT_OK;
}

static bool at_capture(const char *cmd, int timeout_ms, sgm_at_kind_t kind, sgm_at_result_t *out)
{
    out->kind = SGM_AT_OTHER;
    uart_flush_input(SGM_MODEM_UART);
    send_raw(cmd, strlen(cmd));
    send_raw("\r", 1);
    return wait_for(SGM_AT_OK, timeout_ms, kind, out) == SGM_AT_OK && out->kind == kind;
}

static esp_err_t power_on(void)
{
    if (s_powered) {
        return ESP_OK;
    }
    gpio_set_level(SGM_GPIO_MODEM_EN, 1);
    for (int i = 0; i < 100 && !gpio_get_level(SGM_GPIO_MODEM_STATUS); i++) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    for (int i = 0; i < 20; i++) { /* wait for the AT interface */
        if (at("AT", 500)) {
            s_powered = true;
            return ESP_OK;
        }
    }
    return ESP_ERR_TIMEOUT;
}

static esp_err_t cell_connect(void)
{
    uart_setup();
    if (power_on() != ESP_OK) {
        ESP_LOGE(TAG, "modem did not answer");
        return ESP_ERR_TIMEOUT;
    }
    at("ATE0", 500);
    at("AT+CMEE=1", 500);
    at("AT+CTZU=1", 500); /* update RTC from network time (NITZ) */
    if (!at("AT+CPIN?", 5000)) {
        ESP_LOGE(TAG, "SIM not ready");
        return ESP_ERR_INVALID_STATE;
    }
    sgm_at_result_t r;
    bool registered = false;
    for (int i = 0; i < 90 && !registered; i++) { /* up to ~3 minutes for a cold attach */
        registered = at_capture("AT+CEREG?", 1000, SGM_AT_REG, &r) && r.b;
        if (!registered) {
            vTaskDelay(pdMS_TO_TICKS(2000));
        }
    }
    if (!registered) {
        return ESP_ERR_TIMEOUT;
    }
    at_capture("AT+CSQ", 1000, SGM_AT_CSQ, &r);
    char cmd[128];
    snprintf(cmd, sizeof cmd, "AT+QICSGP=1,1,\"%s\",\"\",\"\",1", CONFIG_SGM_CELL_APN);
    at(cmd, 1000);
    at("AT+QIACT=1", 150000); /* returns ERROR if already active; harmless */
    at("AT+QHTTPCFG=\"contextid\",1", 1000);
    at("AT+QHTTPCFG=\"requestheader\",1", 1000);
    return ESP_OK;
}

/* Send a payload after a CONNECT prompt and wait for OK. */
static bool send_after_connect(const char *cmd, const char *data, size_t n, int timeout_ms)
{
    uart_flush_input(SGM_MODEM_UART);
    send_raw(cmd, strlen(cmd));
    send_raw("\r", 1);
    if (wait_for(SGM_AT_CONNECT, timeout_ms, SGM_AT_OTHER, NULL) != SGM_AT_CONNECT) {
        return false;
    }
    send_raw(data, n);
    return wait_for(SGM_AT_OK, timeout_ms, SGM_AT_OTHER, NULL) == SGM_AT_OK;
}

static bool split_url(const char *url, char *host, size_t hn, const char **path)
{
    const char *p = strstr(url, "://");
    p = p ? p + 3 : url;
    const char *slash = strchr(p, '/');
    size_t len = slash ? (size_t)(slash - p) : strlen(p);
    if (len == 0 || len >= hn) {
        return false;
    }
    memcpy(host, p, len);
    host[len] = '\0';
    *path = slash ? slash : "/";
    return true;
}

static esp_err_t cell_post(const char *body, size_t len, int *http_status)
{
    *http_status = 0;
    static char request[8192];
    char host[96];
    const char *path;
    if (!split_url(CONFIG_SGM_API_URL, host, sizeof host, &path)) {
        return ESP_ERR_INVALID_ARG;
    }
    int hdr = snprintf(request, sizeof request,
                       "POST %s HTTP/1.1\r\nHost: %s\r\nAuthorization: Bearer %s\r\n"
                       "Content-Type: application/json\r\nContent-Length: %u\r\nConnection: close\r\n\r\n",
                       path, host, CONFIG_SGM_API_TOKEN, (unsigned)len);
    if (hdr < 0 || (size_t)hdr + len >= sizeof request) {
        return ESP_ERR_INVALID_SIZE;
    }
    memcpy(request + hdr, body, len);
    size_t total = (size_t)hdr + len;

    char cmd[48];
    snprintf(cmd, sizeof cmd, "AT+QHTTPURL=%u,80", (unsigned)strlen(CONFIG_SGM_API_URL));
    if (!send_after_connect(cmd, CONFIG_SGM_API_URL, strlen(CONFIG_SGM_API_URL), 10000)) {
        return ESP_FAIL;
    }
    snprintf(cmd, sizeof cmd, "AT+QHTTPPOST=%u,80,80", (unsigned)total);
    if (!send_after_connect(cmd, request, total, 90000)) {
        return ESP_FAIL;
    }
    sgm_at_result_t r = {0};
    if (wait_for(SGM_AT_HTTP_RESULT, 90000, SGM_AT_HTTP_RESULT, &r) != SGM_AT_HTTP_RESULT || r.a != 0) {
        return ESP_FAIL;
    }
    *http_status = r.b;
    return ESP_OK;
}

static bool cell_time(int64_t *unix_ms, uint8_t *source)
{
    sgm_at_result_t r;
    if (!at_capture("AT+CCLK?", 1000, SGM_AT_CCLK, &r) || r.unix_s < 1700000000) {
        return false; /* modem RTC not yet set from the network */
    }
    *unix_ms = r.unix_s * 1000;
    *source = SGM_TIME_NETWORK;
    return true;
}

static int16_t cell_rssi(void) { return s_rssi; }

static esp_err_t cell_sms(const char *number, const char *text)
{
    if (!number || !*number) {
        return ESP_ERR_INVALID_ARG;
    }
    at("AT+CMGF=1", 1000);
    char cmd[64];
    snprintf(cmd, sizeof cmd, "AT+CMGS=\"%s\"", number);
    uart_flush_input(SGM_MODEM_UART);
    send_raw(cmd, strlen(cmd));
    send_raw("\r", 1);
    if (wait_for(SGM_AT_SMS_PROMPT, 5000, SGM_AT_OTHER, NULL) != SGM_AT_SMS_PROMPT) {
        return ESP_FAIL;
    }
    send_raw(text, strlen(text));
    send_raw("\x1A", 1);
    sgm_at_result_t r;
    return wait_for(SGM_AT_OK, 120000, SGM_AT_CMGS, &r) == SGM_AT_OK ? ESP_OK : ESP_FAIL;
}

static void cell_disconnect(void)
{
    at("AT+QIDEACT=1", 40000);
    if (at("AT+QPOWD=1", 2000)) { /* orderly power-down keeps the modem's flash safe */
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
    gpio_set_level(SGM_GPIO_MODEM_EN, 0);
    s_powered = false;
}

static const sgm_uplink_t CELL = {"cell", cell_connect, cell_post, cell_time, cell_rssi, cell_sms, cell_disconnect};

const sgm_uplink_t *sgm_uplink_cell(void) { return &CELL; }

#else
const sgm_uplink_t *sgm_uplink_cell(void) { return NULL; }
#endif

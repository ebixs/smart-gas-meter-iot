/* sgm_store_io_t on top of ESP-IDF NVS: two blobs, "slot0" and "slot1". */
#include "nvs_store.h"

#include "esp_log.h"
#include "nvs.h"
#include "nvs_flash.h"

static const char *TAG = "nvs_store";
static nvs_handle_t s_handle;

static const char *key(int slot) { return slot ? "slot1" : "slot0"; }

static int nvs_read(void *ctx, int slot, uint8_t *buf, size_t len)
{
    (void)ctx;
    size_t got = len;
    esp_err_t err = nvs_get_blob(s_handle, key(slot), buf, &got);
    return (err == ESP_OK && got == len) ? 0 : 1;
}

static int nvs_write(void *ctx, int slot, const uint8_t *buf, size_t len)
{
    (void)ctx;
    esp_err_t err = nvs_set_blob(s_handle, key(slot), buf, len);
    if (err == ESP_OK) {
        err = nvs_commit(s_handle);
    }
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "write %s failed: %s", key(slot), esp_err_to_name(err));
        return -1;
    }
    return 0;
}

esp_err_t sgm_nvs_store_init(sgm_store_io_t *io)
{
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        /* Only after a partition-layout change; the counter starts over and the
         * boot record reports store_empty so the backend can see it. */
        ESP_LOGW(TAG, "NVS layout changed, erasing");
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    if (err != ESP_OK) {
        return err;
    }
    err = nvs_open("sgm", NVS_READWRITE, &s_handle);
    if (err != ESP_OK) {
        return err;
    }
    io->read = nvs_read;
    io->write = nvs_write;
    io->ctx = NULL;
    return ESP_OK;
}

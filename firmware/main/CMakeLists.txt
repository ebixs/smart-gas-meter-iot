idf_component_register(
    SRCS app_main.c nvs_store.c uplink_wifi.c uplink_cell.c
    INCLUDE_DIRS .
    REQUIRES sgm_core driver esp_timer esp_wifi esp_netif esp_event esp_http_client nvs_flash
             esp_app_format mbedtls)

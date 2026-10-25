# Portable firmware core: no ESP-IDF headers, builds for the ESP32-S3 and for host tests.
set(SGM_CORE_SRCS
    src/at.c
    src/backoff.c
    src/debounce.c
    src/jalali.c
    src/meter.c
    src/period.c
    src/queue.c
    src/sms.c
    src/store.c
    src/telemetry.c)

if(ESP_PLATFORM)
    idf_component_register(SRCS ${SGM_CORE_SRCS} INCLUDE_DIRS include)
else()
    add_library(sgm_core STATIC ${SGM_CORE_SRCS})
    target_include_directories(sgm_core PUBLIC include)
    target_compile_options(sgm_core PRIVATE -Wall -Wextra -Werror -Wconversion -Wno-sign-conversion)
endif()

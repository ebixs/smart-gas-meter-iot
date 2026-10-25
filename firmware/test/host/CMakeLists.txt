# Host build of the portable firmware core: unit tests + a small CLI used by
# the Python cross-checks (tests/test_firmware_core.py).
#   cmake -S firmware/test/host -B build/host && cmake --build build/host && ctest --test-dir build/host
cmake_minimum_required(VERSION 3.16)
project(sgm_firmware_host C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_subdirectory(${CMAKE_CURRENT_LIST_DIR}/../../components/sgm_core ${CMAKE_BINARY_DIR}/sgm_core)

if(NOT MSVC)
    add_compile_options(-Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
    target_compile_options(sgm_core PRIVATE -fsanitize=address,undefined)
endif()

add_executable(test_core test_core.c)
target_link_libraries(test_core PRIVATE sgm_core)

add_executable(sgm_host sgm_host.c)
target_link_libraries(sgm_host PRIVATE sgm_core)

enable_testing()
add_test(NAME core COMMAND test_core)

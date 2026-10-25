/*
 * GPIO map of the v0.2 board (hardware/kicad/design_v02.py, U1 = ESP32-S3-WROOM-1).
 * Module pin -> GPIO per the Espressif WROOM-1 datasheet pin table.
 * tests/test_firmware_core.py checks this file against the design source.
 */
#ifndef SGM_BOARD_H
#define SGM_BOARD_H

#include "driver/gpio.h"

#define SGM_GPIO_PULSE_IN      GPIO_NUM_4   /* module pin 4,  net PULSE_IN (10k pull-up, 1k series) */
#define SGM_GPIO_LED           GPIO_NUM_5   /* module pin 5,  net LED_DRV (active high) */
#define SGM_GPIO_I2C_SDA       GPIO_NUM_6   /* module pin 6,  net I2C_SDA */
#define SGM_GPIO_I2C_SCL       GPIO_NUM_7   /* module pin 7,  net I2C_SCL */
#define SGM_GPIO_TAMPER_IN     GPIO_NUM_15  /* module pin 8,  net TAMPER_IN (high = lid open / wire cut) */
#define SGM_GPIO_MODEM_TXD     GPIO_NUM_17  /* module pin 10, net MODEM_TXD (MCU -> modem) */
#define SGM_GPIO_MODEM_RXD     GPIO_NUM_18  /* module pin 11, net MODEM_RXD (modem -> MCU) */
#define SGM_GPIO_MODEM_EN      GPIO_NUM_9   /* module pin 17, net MODEM_EN (100k pull-down: off at boot) */
#define SGM_GPIO_MODEM_RESET   GPIO_NUM_10  /* module pin 18, net MODEM_RESET (100k pull-down) */
#define SGM_GPIO_MODEM_STATUS  GPIO_NUM_11  /* module pin 19, net MODEM_STATUS (input) */

#define SGM_MODEM_UART         UART_NUM_1

#endif

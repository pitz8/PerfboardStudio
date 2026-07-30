#!/usr/bin/env python3
"""Generate the Perfboard Studio module catalog.

Usage
-----
    python tools/generate_catalog.py            # regenerate everything
    python tools/generate_catalog.py --index    # only rebuild modules/index.json

The generated files under ``modules/`` are the editable source of truth for the
app.  You can hand-edit any of them; just remember that re-running this script
overwrites the families it owns.  To add a one-off part, drop a new .json file
into the right category folder and run ``--index`` to register it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog_lib import (  # noqa: E402
    COL, axial_diode, axial_resistor, breakout, ceramic_cap, circle, col_pins,
    devboard, dip, electrolytic, ellipse, header, ic_socket, led, line, path,
    pin, polygon, r4, rect, row_pins, text, to92, to220,
)

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"

CATEGORIES = [
    {"id": "mcu", "name": "MCU & Dev Boards", "color": "#7aa2f7"},
    {"id": "ic", "name": "Integrated Circuits", "color": "#9d7cd8"},
    {"id": "power", "name": "Power & Regulators", "color": "#e0af68"},
    {"id": "sensor", "name": "Sensors", "color": "#73daca"},
    {"id": "display", "name": "Displays & Indicators", "color": "#7dcfff"},
    {"id": "passive", "name": "Passives", "color": "#c0caf5"},
    {"id": "discrete", "name": "Diodes, LEDs & Transistors", "color": "#f7768e"},
    {"id": "connector", "name": "Connectors & Switches", "color": "#ff9e64"},
    {"id": "comms", "name": "Wireless & Comms", "color": "#41a6b5"},
    {"id": "motor", "name": "Motors & Drivers", "color": "#bb9af7"},
    {"id": "misc", "name": "Misc & Mechanical", "color": "#a9b1d6"},
]

BUILT: list[dict] = []


def add(mod):
    BUILT.append(mod)
    return mod


# ===========================================================================
# MCU & dev boards
# ===========================================================================

# Shared by every RP2040/RP2350 Pico-form-factor board.
PICO_LEFT = ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6", "GP7",
             "GP8", "GP9", "GND", "GP10", "GP11", "GP12", "GP13", "GND", "GP14", "GP15"]
PICO_RIGHT = ["VBUS", "VSYS", "GND", "3V3EN", "3V3", "ADCREF", "GP28", "GND", "GP27",
              "GP26", "RUN", "GP22", "GND", "GP21", "GP20", "GP19", "GP18", "GND",
              "GP17", "GP16"]

# The 38-pin ESP32-WROOM carrier, 19 pins per side.  Sold with either a
# micro-USB or a USB-C socket, and with either the PCB trace antenna
# (WROOM-32/32D) or a U.FL/IPEX socket (WROOM-32U).  All share this pinout.
WROOM38_LEFT = ["3V3", "EN", "GPIO36", "GPIO39", "GPIO34", "GPIO35", "GPIO32",
                "GPIO33", "GPIO25", "GPIO26", "GPIO27", "GPIO14", "GPIO12", "GND",
                "GPIO13", "SD2", "SD3", "CMD", "5V"]
WROOM38_RIGHT = ["GND", "GPIO23", "GPIO22", "TX0", "RX0", "GPIO21", "GND", "GPIO19",
                 "GPIO18", "GPIO5", "GPIO17", "GPIO16", "GPIO4", "GPIO0", "GPIO2",
                 "GPIO15", "SD1", "SD0", "CLK"]

# Every Seeed XIAO shares one 2×7 pinout, whatever MCU is on top.
XIAO_LEFT = ["D0/A0", "D1/A1", "D2/A2", "D3/A3", "D4/SDA", "D5/SCL", "D6/TX"]
XIAO_RIGHT = ["5V", "GND", "3V3", "D10/MOSI", "D9/MISO", "D8/SCK", "D7/RX"]


def build_mcu():
    add(devboard(
        "esp32-c3-supermini", "ESP32-C3 SuperMini", "RISC-V Wi-Fi + BLE",
        ["5V", "GND", "3V3", "GPIO4", "GPIO3", "GPIO2", "GPIO1", "GPIO0"],
        ["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO20", "GPIO21"],
        span=6, pcb=COL["pcb_black"], mark="ESP32-C3",
        tags=["esp32", "espressif", "wifi", "ble", "riscv"],
        datasheet="https://www.espressif.com/en/products/socs/esp32-c3",
    ))
    add(devboard(
        "esp32-devkit-v1", "ESP32 DevKit V1", "30-pin ESP-WROOM-32",
        ["3V3", "EN", "GPIO36", "GPIO39", "GPIO34", "GPIO35", "GPIO32", "GPIO33",
         "GPIO25", "GPIO26", "GPIO27", "GPIO14", "GPIO12", "GPIO13", "GND"],
        ["VIN", "GND", "GPIO23", "GPIO22", "GPIO1", "GPIO3", "GPIO21", "GPIO19",
         "GPIO18", "GPIO5", "GPIO17", "GPIO16", "GPIO4", "GPIO2", "GPIO15"],
        span=10, pcb=COL["pcb_black"], mark="ESP32 DevKit",
        tags=["esp32", "espressif", "wifi", "ble", "doit"],
    ))
    add(devboard(
        "esp32-s3-devkitc", "ESP32-S3 DevKitC", "44-pin, USB-OTG",
        ["3V3", "3V3", "RST", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO15",
         "GPIO16", "GPIO17", "GPIO18", "GPIO8", "GPIO3", "GPIO46", "GPIO9",
         "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO14", "5V", "GND"],
        ["GND", "GPIO43", "GPIO44", "GPIO1", "GPIO2", "GPIO42", "GPIO41", "GPIO40",
         "GPIO39", "GPIO38", "GPIO37", "GPIO36", "GPIO35", "GPIO0", "GPIO45",
         "GPIO48", "GPIO47", "GPIO21", "GPIO20", "GPIO19", "GND", "GND"],
        span=10, pcb=COL["pcb_black"], mark="ESP32-S3",
        tags=["esp32", "s3", "espressif", "wifi", "ble"],
    ))
    add(devboard(
        "esp8266-d1-mini", "WeMos D1 Mini", "ESP8266 Wi-Fi",
        ["RST", "A0", "D0", "D5", "D6", "D7", "D8", "3V3"],
        ["TX", "RX", "D1", "D2", "D3", "D4", "GND", "5V"],
        span=9, pcb=COL["pcb_black"], mark="D1 mini",
        tags=["esp8266", "wemos", "wifi", "lolin"],
    ))
    add(devboard(
        "esp8266-nodemcu-v3", "NodeMCU V3", "ESP8266 LoLin",
        ["A0", "RSV", "RSV", "SD3", "SD2", "SD1", "CMD", "SD0", "CLK", "GND",
         "3V3", "EN", "RST", "GND", "VIN"],
        ["D0", "D1", "D2", "D3", "D4", "3V3", "GND", "D5", "D6", "D7", "D8",
         "RX", "TX", "GND", "3V3"],
        span=11, pcb=COL["pcb_black"], mark="NodeMCU",
        tags=["esp8266", "nodemcu", "wifi", "lolin"],
    ))
    add(devboard(
        "arduino-nano", "Arduino Nano", "ATmega328P",
        ["D1/TX", "D0/RX", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7",
         "D8", "D9", "D10", "D11", "D12"],
        ["VIN", "GND", "RST", "5V", "A7", "A6", "A5", "A4", "A3", "A2", "A1",
         "A0", "AREF", "3V3", "D13"],
        span=6, pcb=COL["pcb_blue"], pcb_edge=COL["pcb_blue_edge"], mark="NANO",
        tags=["arduino", "avr", "atmega328p"],
    ))
    add(devboard(
        "arduino-pro-micro", "Pro Micro", "ATmega32U4, 5 V",
        ["TX0", "RX1", "GND", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"],
        ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0", "D15", "D14", "D16", "D10"],
        span=6, pcb=COL["pcb_black"], mark="PRO MICRO",
        tags=["arduino", "atmega32u4", "usb", "hid"],
    ))
    add(devboard(
        "rpi-pico", "Raspberry Pi Pico", "RP2040",
        PICO_LEFT, PICO_RIGHT,
        span=7, pcb="#1a5c3a", pcb_edge="#0d3a23", mark="PICO",
        tags=["raspberry", "rp2040", "pico"],
        datasheet="https://www.raspberrypi.com/documentation/microcontrollers/",
    ))
    add(devboard(
        "rpi-pico-w", "Raspberry Pi Pico W", "RP2040 + Wi-Fi",
        PICO_LEFT, PICO_RIGHT,
        span=7, pcb="#1a5c3a", pcb_edge="#0d3a23", mark="PICO W",
        tags=["raspberry", "rp2040", "pico", "wifi"],
    ))
    add(devboard(
        "stm32-blue-pill", "STM32 Blue Pill", "STM32F103C8T6",
        ["VBAT", "PC13", "PC14", "PC15", "PA0", "PA1", "PA2", "PA3", "PA4", "PA5",
         "PA6", "PA7", "PB0", "PB1", "PB10", "PB11", "RST", "3V3", "GND", "GND"],
        ["3V3", "GND", "5V", "PB9", "PB8", "PB7", "PB6", "PB5", "PB4", "PB3",
         "PA15", "PA12", "PA11", "PA10", "PA9", "PA8", "PB15", "PB14", "PB13", "PB12"],
        span=8, pcb=COL["pcb_blue"], pcb_edge=COL["pcb_blue_edge"], mark="BLUE PILL",
        tags=["stm32", "arm", "cortex-m3"],
    ))
    add(devboard(
        "xiao-esp32c3", "Seeed XIAO ESP32-C3", "thumbnail-sized",
        XIAO_LEFT, XIAO_RIGHT,
        span=5, pcb=COL["pcb_black"], mark="XIAO",
        tags=["seeed", "xiao", "esp32", "c3"],
    ))
    add(devboard(
        "teensy-40", "Teensy 4.0", "600 MHz Cortex-M7",
        ["GND", "D0/RX1", "D1/TX1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
         "D9", "D10", "D11", "D12"],
        ["VIN", "GND", "3V3", "A9", "A8", "A7", "A6", "A5", "A4", "A3", "A2",
         "A1", "A0", "D13"],
        span=6, pcb=COL["pcb_black"], mark="TEENSY 4.0",
        tags=["teensy", "pjrc", "imxrt1062"],
    ))
    add(breakout(
        "attiny85-digispark", "Digispark", "ATtiny85 USB board",
        ["P5", "P4", "P3", "P2", "P1", "P0"],
        cols=6, rows=5, category="mcu", pcb=COL["pcb_red"], pcb_edge="#4a0f18",
        mark="DIGISPARK", tags=["attiny85", "digispark", "usb"],
    ))
    add(devboard(
        "esp32-wroom-u-typec", "ESP32-WROOM-32U USB-C", "38-pin, 19 per side, U.FL antenna",
        WROOM38_LEFT, WROOM38_RIGHT,
        span=10, pcb=COL["pcb_black"], mark="WROOM-32U", usb="none",
        tags=["esp32", "wroom", "wroom-32u", "usb-c", "type-c", "38-pin", "19-pin",
              "ipex", "u.fl", "external antenna", "espressif", "wifi", "ble"],
        datasheet="https://www.espressif.com/en/products/modules/esp32",
        extra_shapes=[
            # USB-C receptacle on the bottom edge
            rect(4.25, 18.02, 1.5, 0.52, COL["tin"], "#7f868e", rx=0.26),
            # U.FL / IPEX antenna socket beside the shield can
            circle(8.7, 8.7, 0.52, COL["steel"], "#6f767e", sw=0.06),
            circle(8.7, 8.7, 0.2, COL["gold"]),
            # BOOT and EN buttons
            rect(0.45, 17.1, 0.9, 0.9, COL["plastic_black"], "#3a4048", rx=0.08),
            rect(8.65, 17.1, 0.9, 0.9, COL["plastic_black"], "#3a4048", rx=0.08),
        ],
    ))
    add(devboard(
        "esp32-devkit-38pin", "ESP32 DevKitC 38-pin", "WROOM-32, micro-USB",
        WROOM38_LEFT, WROOM38_RIGHT,
        span=10, pcb=COL["pcb_black"], mark="ESP32 DevKitC", usb="bottom",
        tags=["esp32", "wroom", "devkitc", "38-pin", "espressif", "wifi", "ble"],
    ))
    add(devboard(
        "esp32-c6-supermini", "ESP32-C6 SuperMini", "Wi-Fi 6, BLE 5, Zigbee",
        ["5V", "GND", "3V3", "GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4"],
        ["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO21", "GPIO22", "GPIO23"],
        span=6, pcb=COL["pcb_black"], mark="ESP32-C6",
        tags=["esp32", "c6", "wifi6", "zigbee", "thread", "ble", "espressif", "riscv"],
    ))
    add(devboard(
        "esp32-s2-mini", "Lolin S2 Mini", "ESP32-S2, USB-C",
        ["GND", "GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6",
         "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO14"],
        ["3V3", "RST", "GPIO40", "GPIO39", "GPIO38", "GPIO37", "GPIO36", "GPIO35",
         "GPIO34", "GPIO33", "GPIO21", "GPIO18", "GPIO17", "GPIO16", "GPIO15", "5V"],
        span=6, pcb=COL["pcb_black"], mark="S2 MINI",
        tags=["esp32", "s2", "lolin", "wemos", "usb-c", "wifi"],
    ))
    add(devboard(
        "esp32-cam", "ESP32-CAM", "AI-Thinker, OV2640 camera",
        ["5V", "GND", "GPIO12", "GPIO13", "GPIO15", "GPIO14", "GPIO2", "GPIO4"],
        ["3V3", "GND", "GPIO16", "GPIO0", "GND", "VCC", "U0R", "U0T"],
        span=9, pcb=COL["pcb_black"], mark="ESP32-CAM", usb="none",
        tags=["esp32", "camera", "ov2640", "ai-thinker", "wifi", "video"],
        extra_shapes=[
            # camera ribbon socket and the microSD slot on the underside
            rect(1.6, -0.2, 6.8, 1.1, "#3a4048", "#22262c", rx=0.08),
            rect(1.2, 5.4, 7.6, 1.9, "#2f343b", "#14171a", rx=0.1),
        ],
    ))
    add(devboard(
        "esp-12f-adapter", "ESP-12F adapter", "ESP8266 module on a DIP carrier",
        ["RST", "ADC", "EN", "GPIO16", "GPIO14", "GPIO12", "GPIO13", "VCC"],
        ["TXD", "RXD", "GPIO5", "GPIO4", "GPIO0", "GPIO2", "GPIO15", "GND"],
        span=9, pcb=COL["pcb_black"], mark="ESP-12F", usb="none",
        tags=["esp8266", "esp-12f", "esp-12e", "adapter", "wifi"],
    ))
    add(devboard(
        "arduino-pro-mini", "Arduino Pro Mini", "ATmega328P, 5 V / 16 MHz",
        ["TXO", "RXI", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"],
        ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0", "D13", "D12", "D11", "D10"],
        span=6, pcb=COL["pcb_blue"], pcb_edge=COL["pcb_blue_edge"], mark="PRO MINI",
        usb="none", tags=["arduino", "pro mini", "atmega328p", "avr"],
    ))
    add(devboard(
        "arduino-micro", "Arduino Micro", "ATmega32U4, native USB",
        ["D1/TX", "D0/RX", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
         "D9", "D10", "D11", "D12", "D13", "3V3", "AREF"],
        ["5V", "GND", "GND", "VIN", "A0", "A1", "A2", "A3", "A4", "A5", "SCK",
         "MOSI", "MISO", "RST", "GND", "D14", "D15", "D16"],
        span=6, pcb=COL["pcb_blue"], pcb_edge=COL["pcb_blue_edge"], mark="MICRO",
        tags=["arduino", "micro", "atmega32u4", "hid", "usb"],
    ))
    add(devboard(
        "stm32-black-pill", "STM32 Black Pill", "STM32F411CEU6, USB-C",
        ["VB", "PC13", "PC14", "PC15", "PH0", "PH1", "RST", "PA0", "PA1", "PA2",
         "PA3", "PA4", "PA5", "PA6", "PA7", "PB0", "PB1", "PB2", "PB10", "3V3"],
        ["GND", "5V", "3V3", "PB9", "PB8", "PB7", "PB6", "PB5", "PB4", "PB3",
         "PA15", "PA12", "PA11", "PA10", "PA9", "PA8", "PB15", "PB14", "PB13", "PB12"],
        span=8, pcb=COL["pcb_black"], mark="BLACK PILL",
        tags=["stm32", "f411", "black pill", "arm", "cortex-m4", "usb-c"],
    ))
    add(devboard(
        "rpi-pico-2", "Raspberry Pi Pico 2", "RP2350, dual Cortex-M33",
        PICO_LEFT, PICO_RIGHT,
        span=7, pcb="#1a5c3a", pcb_edge="#0d3a23", mark="PICO 2",
        tags=["raspberry", "rp2350", "pico", "pico2"],
    ))
    add(devboard(
        "rp2040-zero", "Waveshare RP2040-Zero", "thumb-sized RP2040, USB-C",
        ["5V", "GND", "3V3", "GP29", "GP28", "GP27", "GP26", "GP15", "GP14"],
        ["GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8"],
        span=6, pcb=COL["pcb_black"], mark="RP2040-ZERO",
        tags=["raspberry", "rp2040", "waveshare", "zero", "usb-c"],
    ))
    add(devboard(
        "xiao-rp2040", "Seeed XIAO RP2040", "thumbnail-sized RP2040",
        XIAO_LEFT, XIAO_RIGHT,
        span=5, pcb=COL["pcb_purple"], pcb_edge="#1c1029", mark="XIAO 2040",
        tags=["seeed", "xiao", "rp2040"],
    ))
    add(devboard(
        "xiao-nrf52840", "Seeed XIAO nRF52840", "BLE 5.0, thumbnail-sized",
        XIAO_LEFT, XIAO_RIGHT,
        span=5, pcb=COL["pcb_black"], mark="XIAO BLE",
        tags=["seeed", "xiao", "nrf52840", "ble", "bluetooth"],
    ))
    add(devboard(
        "xiao-samd21", "Seeed XIAO SAMD21", "Cortex-M0+, USB-C",
        XIAO_LEFT, XIAO_RIGHT,
        span=5, pcb=COL["pcb_black"], mark="XIAO M0",
        tags=["seeed", "xiao", "samd21", "seeeduino"],
    ))
    add(devboard(
        "teensy-41", "Teensy 4.1", "600 MHz, Ethernet + microSD",
        ["GND", "D0/RX1", "D1/TX1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9",
         "D10", "D11", "D12", "D24", "D25", "D26", "D27", "D28", "D29", "D30",
         "D31", "D32", "D33"],
        ["VIN", "GND", "3V3", "D23", "D22", "D21", "D20", "D19", "D18", "D17",
         "D16", "D15", "D14", "D13", "D41", "D40", "D39", "D38", "D37", "D36",
         "D35", "D34", "GND", "3V3"],
        span=6, pcb=COL["pcb_black"], mark="TEENSY 4.1",
        tags=["teensy", "pjrc", "imxrt1062", "ethernet"],
    ))


# ===========================================================================
# DIP integrated circuits
# ===========================================================================

def build_ic():
    add(dip("ne555", "NE555", "Timer", ["GND", "TRIG", "OUT", "RST"],
            ["VCC", "DIS", "THR", "CTRL"], mark="555", tags=["timer", "oscillator"]))
    add(dip("lm358", "LM358", "Dual op-amp", ["OUT1", "IN1-", "IN1+", "V-"],
            ["V+", "OUT2", "IN2-", "IN2+"], mark="LM358", tags=["opamp", "analog"]))
    add(dip("tl072", "TL072", "Dual JFET op-amp", ["OUT1", "IN1-", "IN1+", "V-"],
            ["V+", "OUT2", "IN2-", "IN2+"], mark="TL072", tags=["opamp", "audio"]))
    add(dip("lm393", "LM393", "Dual comparator", ["OUT1", "IN1-", "IN1+", "GND"],
            ["VCC", "OUT2", "IN2-", "IN2+"], mark="LM393", tags=["comparator"]))
    add(dip("lm386", "LM386", "Audio amplifier", ["GAIN", "IN-", "IN+", "GND"],
            ["GAIN", "BYPASS", "VS", "VOUT"], mark="LM386", tags=["audio", "amplifier"]))
    add(dip("lm324", "LM324", "Quad op-amp",
            ["OUT1", "IN1-", "IN1+", "V+", "IN2+", "IN2-", "OUT2"],
            ["OUT4", "IN4-", "IN4+", "V-", "IN3+", "IN3-", "OUT3"],
            mark="LM324", tags=["opamp", "analog"]))
    add(dip("74hc595", "74HC595", "8-bit shift register",
            ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "GND"],
            ["VCC", "Q0", "DS", "OE", "STCP", "SHCP", "MR", "Q7S"],
            mark="74HC595", tags=["shift register", "logic", "serial"]))
    add(dip("74hc165", "74HC165", "Parallel-in shift register",
            ["PL", "CP", "D4", "D5", "D6", "D7", "Q7N", "GND"],
            ["VCC", "CE", "D3", "D2", "D1", "D0", "DS", "Q7"],
            mark="74HC165", tags=["shift register", "logic"]))
    add(dip("74hc00", "74HC00", "Quad 2-input NAND",
            ["1A", "1B", "1Y", "2A", "2B", "2Y", "GND"],
            ["VCC", "4B", "4A", "4Y", "3B", "3A", "3Y"],
            mark="74HC00", tags=["logic", "nand", "gate"]))
    add(dip("74hc14", "74HC14", "Hex Schmitt inverter",
            ["1A", "1Y", "2A", "2Y", "3A", "3Y", "GND"],
            ["VCC", "6A", "6Y", "5A", "5Y", "4A", "4Y"],
            mark="74HC14", tags=["logic", "inverter", "schmitt"]))
    add(dip("cd4017", "CD4017", "Decade counter / divider",
            ["Q5", "Q1", "Q0", "Q2", "Q6", "Q7", "Q3", "GND"],
            ["VDD", "RST", "CLK", "CLKEN", "CO", "Q9", "Q4", "Q8"],
            mark="CD4017", tags=["cmos", "counter", "logic"]))
    add(dip("uln2003", "ULN2003", "7-ch Darlington array",
            ["IN1", "IN2", "IN3", "IN4", "IN5", "IN6", "IN7", "GND"],
            ["OUT1", "OUT2", "OUT3", "OUT4", "OUT5", "OUT6", "OUT7", "COM"],
            mark="ULN2003", tags=["driver", "darlington", "relay"]))
    add(dip("l293d", "L293D", "Dual H-bridge",
            ["EN1", "IN1", "OUT1", "GND", "GND", "OUT2", "IN2", "VS"],
            ["VSS", "IN4", "OUT4", "GND", "GND", "OUT3", "IN3", "EN2"],
            mark="L293D", tags=["motor", "h-bridge", "driver"], category="motor"))
    add(dip("pcf8574", "PCF8574", "I2C 8-bit I/O expander",
            ["A0", "A1", "A2", "P0", "P1", "P2", "P3", "GND"],
            ["VDD", "SDA", "SCL", "INT", "P7", "P6", "P5", "P4"],
            mark="PCF8574", tags=["i2c", "gpio", "expander"]))
    add(dip("ds1307", "DS1307", "I2C real-time clock",
            ["X1", "X2", "VBAT", "GND"], ["VCC", "SQW", "SCL", "SDA"],
            mark="DS1307", tags=["rtc", "i2c", "clock"]))
    add(dip("24lc256", "24LC256", "32 KB I2C EEPROM",
            ["A0", "A1", "A2", "GND"], ["VCC", "WP", "SCL", "SDA"],
            mark="24LC256", tags=["eeprom", "i2c", "memory"]))
    add(dip("attiny85-dip", "ATtiny85", "8-bit AVR, DIP-8",
            ["RST/PB5", "PB3", "PB4", "GND"], ["VCC", "PB2", "PB1", "PB0"],
            mark="ATtiny85", tags=["avr", "microcontroller"], category="mcu"))
    add(dip("atmega328p-dip", "ATmega328P", "8-bit AVR, DIP-28",
            ["RST", "D0/RX", "D1/TX", "D2", "D3", "D4", "VCC", "GND", "XTAL1",
             "XTAL2", "D5", "D6", "D7", "D8"],
            ["A5", "A4", "A3", "A2", "A1", "A0", "GND", "AREF", "AVCC", "D13",
             "D12", "D11", "D10", "D9"],
            mark="ATmega328P", tags=["avr", "arduino", "microcontroller"], category="mcu"))
    add(dip("mcp23017", "MCP23017", "I2C 16-bit I/O expander",
            ["GPB0", "GPB1", "GPB2", "GPB3", "GPB4", "GPB5", "GPB6", "GPB7",
             "VDD", "VSS", "NC", "SCL", "SDA", "NC"],
            ["GPA7", "GPA6", "GPA5", "GPA4", "GPA3", "GPA2", "GPA1", "GPA0",
             "INTA", "INTB", "RST", "A2", "A1", "A0"],
            mark="MCP23017", tags=["i2c", "gpio", "expander"]))
    add(dip("pc817", "PC817", "Optocoupler", ["A", "K"], ["C", "E"],
            mark="817", tags=["optocoupler", "isolation"]))
    add(dip("mcp2515-dip", "MCP2515", "CAN controller",
            ["TXCAN", "RXCAN", "CLKOUT", "TX0RTS", "TX1RTS", "TX2RTS", "OSC2",
             "OSC1", "VSS"],
            ["VDD", "RESET", "CS", "SO", "SI", "SCK", "INT", "RX0BF", "RX1BF"],
            mark="MCP2515", tags=["can", "spi", "bus"], category="comms"))

    # Blank packages, for anything not in the catalogue yet.
    for n, wide in ((8, False), (14, False), (16, False), (18, False), (20, False),
                    (24, True), (28, False), (40, True)):
        rows = n // 2
        add(dip(f"dip-{n}-blank", f"DIP-{n}", "blank package",
                [""] * rows, [""] * rows, wide=wide,
                mark=f"DIP-{n}", tags=["blank", "generic", "placeholder"]))

    # -- 74HC / CD4000 logic ------------------------------------------------
    # `dip` takes the right-hand column top-to-bottom, i.e. the highest pin
    # number first, because that is how the package reads on the bench.
    add(dip("74hc04", "74HC04", "Hex inverter",
            ["1A", "1Y", "2A", "2Y", "3A", "3Y", "GND"],
            ["VCC", "6A", "6Y", "5A", "5Y", "4A", "4Y"],
            mark="74HC04", tags=["logic", "inverter", "not", "cmos"]))
    add(dip("74hc08", "74HC08", "Quad 2-input AND",
            ["1A", "1B", "1Y", "2A", "2B", "2Y", "GND"],
            ["VCC", "4B", "4A", "4Y", "3B", "3A", "3Y"],
            mark="74HC08", tags=["logic", "and", "gate", "cmos"]))
    add(dip("74hc32", "74HC32", "Quad 2-input OR",
            ["1A", "1B", "1Y", "2A", "2B", "2Y", "GND"],
            ["VCC", "4B", "4A", "4Y", "3B", "3A", "3Y"],
            mark="74HC32", tags=["logic", "or", "gate", "cmos"]))
    add(dip("74hc86", "74HC86", "Quad 2-input XOR",
            ["1A", "1B", "1Y", "2A", "2B", "2Y", "GND"],
            ["VCC", "4B", "4A", "4Y", "3B", "3A", "3Y"],
            mark="74HC86", tags=["logic", "xor", "gate", "cmos"]))
    add(dip("74hc74", "74HC74", "Dual D flip-flop",
            ["1CLR", "1D", "1CLK", "1PRE", "1Q", "1/Q", "GND"],
            ["VCC", "2CLR", "2D", "2CLK", "2PRE", "2Q", "2/Q"],
            mark="74HC74", tags=["logic", "flip-flop", "register", "cmos"]))
    add(dip("74hc138", "74HC138", "3-to-8 line decoder",
            ["A0", "A1", "A2", "E1", "E2", "E3", "Y7", "GND"],
            ["VCC", "Y0", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6"],
            mark="74HC138", tags=["logic", "decoder", "demux", "cmos"]))
    add(dip("74hc4051", "74HC4051", "8-channel analogue mux",
            ["Y4", "Y6", "Z", "Y7", "Y5", "E", "VEE", "GND"],
            ["VCC", "Y2", "Y1", "Y0", "Y3", "S0", "S1", "S2"],
            mark="74HC4051", tags=["mux", "multiplexer", "analog", "switch"]))
    add(dip("74hc245", "74HC245", "Octal bus transceiver",
            ["DIR", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "GND"],
            ["VCC", "OE", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"],
            mark="74HC245", tags=["logic", "buffer", "bus", "level"]))
    add(dip("cd4013", "CD4013", "Dual D flip-flop",
            ["Q1", "/Q1", "CLK1", "RST1", "D1", "SET1", "VSS"],
            ["VDD", "Q2", "/Q2", "CLK2", "RST2", "D2", "SET2"],
            mark="CD4013", tags=["logic", "flip-flop", "cmos", "4000"]))
    add(dip("cd4026", "CD4026", "Decade counter, 7-seg out",
            ["CLK", "INH", "DEI", "Qc", "CO", "Qd", "Qa", "VSS"],
            ["VDD", "UCS", "Qb", "DEO", "RST", "Qg", "Qf", "Qe"],
            mark="CD4026", tags=["counter", "7-segment", "cmos", "4000"]))
    add(dip("cd4511", "CD4511", "BCD to 7-segment latch/driver",
            ["B", "C", "LE", "BL", "LT", "D", "A", "VSS"],
            ["VDD", "f", "g", "a", "b", "c", "d", "e"],
            mark="CD4511", tags=["decoder", "7-segment", "bcd", "driver"]))
    add(dip("cd4066", "CD4066", "Quad bilateral switch",
            ["1A", "1B", "2B", "2A", "CTL2", "CTL1", "VSS"],
            ["VDD", "3A", "3B", "4B", "4A", "CTL3", "CTL4"],
            mark="CD4066", tags=["switch", "analog", "cmos", "4000"]))

    # -- op-amps, comparators, converters -----------------------------------
    add(dip("lm741", "LM741", "General-purpose op-amp",
            ["OFF1", "IN-", "IN+", "V-"], ["NC", "V+", "OUT", "OFF2"],
            mark="741", tags=["op-amp", "amplifier", "analog"]))
    add(dip("ne5532", "NE5532", "Low-noise dual op-amp",
            ["OUTA", "INA-", "INA+", "V-"], ["V+", "OUTB", "INB-", "INB+"],
            mark="5532", tags=["op-amp", "audio", "low noise", "dual"]))
    add(dip("lm339", "LM339", "Quad comparator",
            ["OUT2", "OUT1", "V+", "IN1-", "IN1+", "IN2-", "IN2+"],
            ["OUT3", "OUT4", "GND", "IN4+", "IN4-", "IN3+", "IN3-"],
            mark="339", tags=["comparator", "quad", "analog"]))
    add(dip("mcp3008", "MCP3008", "8-channel 10-bit ADC, SPI",
            ["CH0", "CH1", "CH2", "CH3", "CH4", "CH5", "CH6", "CH7"],
            ["VDD", "VREF", "AGND", "CLK", "DOUT", "DIN", "CS", "DGND"],
            mark="MCP3008", tags=["adc", "spi", "analog", "10-bit"]))
    add(dip("uln2803", "ULN2803", "Octal Darlington driver",
            ["IN1", "IN2", "IN3", "IN4", "IN5", "IN6", "IN7", "IN8", "GND"],
            ["OUT1", "OUT2", "OUT3", "OUT4", "OUT5", "OUT6", "OUT7", "OUT8", "COM"],
            mark="ULN2803", tags=["driver", "darlington", "relay", "sink"]))

    add(breakout("ads1115-module", "ADS1115", "4-channel 16-bit ADC, I2C",
                 ["VDD", "GND", "SCL", "SDA", "ADDR", "ALRT", "A0", "A1", "A2", "A3"],
                 cols=10, rows=6, category="ic", pcb=COL["pcb_purple"],
                 pcb_edge="#1c1029", mark="ADS1115", label_size=0.5,
                 tags=["adc", "i2c", "16-bit", "analog", "converter"]))
    add(breakout("mcp4725-module", "MCP4725", "12-bit DAC, I2C",
                 ["OUT", "GND", "SCL", "SDA", "VCC"], cols=5, rows=6,
                 category="ic", pcb=COL["pcb_purple"], pcb_edge="#1c1029",
                 mark="MCP4725", tags=["dac", "i2c", "12-bit", "analog"]))
    add(breakout("pcf8591-module", "PCF8591", "4-ch ADC + 1-ch DAC, I2C",
                 ["AOUT", "AIN0", "AIN1", "AIN2", "AIN3", "SCL", "SDA", "VCC", "GND"],
                 cols=12, rows=9, category="ic", pcb=COL["pcb_blue"],
                 mark="PCF8591", label_size=0.5,
                 tags=["adc", "dac", "i2c", "8-bit", "analog"]))


# ===========================================================================
# Power
# ===========================================================================

def build_power():
    for mid, name, v in (("lm7805", "LM7805", "5 V"), ("lm7809", "LM7809", "9 V"),
                         ("lm7812", "LM7812", "12 V"), ("lm7815", "LM7815", "15 V"),
                         ("lm7905", "LM7905", "-5 V")):
        add(to220(mid, name, f"{v} linear regulator", ["IN", "GND", "OUT"],
                  mark=name.replace("LM", ""), tags=["regulator", "linear", v]))
    add(to220("lm317", "LM317", "adjustable regulator", ["ADJ", "OUT", "IN"],
              mark="317", tags=["regulator", "linear", "adjustable"]))
    add(to92("ams1117-33-to92", "LD1117-3.3", "3.3 V LDO (TO-92)",
             ["GND", "OUT", "IN"], category="power", mark="1117",
             tags=["regulator", "ldo", "3v3"], designator="U"))

    add(breakout("ams1117-33-module", "AMS1117-3.3 module", "3.3 V LDO breakout",
                 ["VIN", "GND", "3V3"], cols=3, rows=3, category="power",
                 pcb=COL["pcb_blue"], mark="AMS1117", tags=["regulator", "ldo", "3v3"]))
    add(breakout("mp1584en", "MP1584EN mini buck", "3 A step-down",
                 ["VIN", "GND", "GND", "VOUT"], cols=6, rows=5, category="power",
                 pcb=COL["pcb_black"], mark="MP1584EN",
                 tags=["buck", "step-down", "switching", "dc-dc"]))
    add(breakout("lm2596-module", "LM2596 buck module", "3 A adjustable step-down",
                 ["IN+", "IN-", "OUT-", "OUT+"], cols=17, rows=9, category="power",
                 pcb=COL["pcb_red"], pcb_edge="#4a0f18", mark="LM2596",
                 tags=["buck", "step-down", "switching", "dc-dc"], label_size=0.5))
    add(breakout("mt3608-module", "MT3608 boost", "2 A step-up",
                 ["VIN+", "VIN-", "VOUT-", "VOUT+"], cols=14, rows=6, category="power",
                 pcb=COL["pcb_blue"], mark="MT3608",
                 tags=["boost", "step-up", "switching", "dc-dc"]))
    add(breakout("xl6009-module", "XL6009 boost", "4 A step-up",
                 ["IN+", "IN-", "OUT-", "OUT+"], cols=17, rows=9, category="power",
                 pcb=COL["pcb_red"], pcb_edge="#4a0f18", mark="XL6009",
                 tags=["boost", "step-up", "dc-dc"], label_size=0.5))
    add(breakout("tp4056-module", "TP4056 charger", "1-cell Li-ion / LiPo",
                 ["IN+", "IN-", "BAT+", "BAT-", "OUT+", "OUT-"],
                 cols=10, rows=8, category="power", pcb=COL["pcb_blue"], mark="TP4056",
                 tags=["charger", "lithium", "lipo", "18650", "battery"]))
    add(breakout("ina219-module", "INA219", "I2C current / power monitor",
                 ["VCC", "GND", "SCL", "SDA", "VIN+", "VIN-"],
                 cols=8, rows=6, category="power", pcb=COL["pcb_purple"],
                 pcb_edge="#1c1029", mark="INA219",
                 tags=["current", "i2c", "measurement", "power"]))

    # Bridge rectifier, 4 in-line pins.
    add({
        "id": "bridge-rectifier-db107",
        "name": "Bridge rectifier DB107",
        "subtitle": "1 A, 1000 V",
        "category": "power",
        "tags": ["rectifier", "bridge", "diode", "ac"],
        "designator": "BR",
        "footprint": {"cols": 4, "rows": 1},
        "pins": [pin(0, 0, "AC", 1, "in"), pin(1, 0, "-", 2, "gnd"),
                 pin(2, 0, "AC", 3, "in"), pin(3, 0, "+", 4, "power")],
        "body": {"x": -0.4, "y": -1.5, "w": 3.8, "h": 1.1, "rx": 0.1,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [line(c, 0, c, -0.4, COL["tin"], 0.11) for c in range(4)]
                  + [text(1.5, -0.95, "DB107", size=0.32, color=COL["ic_mark"])],
    })
    # KBL/KBP style bridge: 4 leads on 5 mm centres, so every other hole.
    add({
        "id": "bridge-rectifier-kbl406",
        "name": "Bridge rectifier KBL406",
        "subtitle": "4 A, 600 V",
        "category": "power",
        "tags": ["rectifier", "bridge", "diode", "ac", "kbl"],
        "designator": "BR",
        "footprint": {"cols": 7, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(2, 0, "AC", 2, "in"),
                 pin(4, 0, "AC", 3, "in"), pin(6, 0, "-", 4, "gnd")],
        "body": {"x": -0.6, "y": -3.4, "w": 7.2, "h": 3.0, "rx": 0.4,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [line(c, 0, c, -0.4, COL["tin"], 0.12) for c in (0, 2, 4, 6)]
                  + [circle(3.0, -3.0, 0.4, "#0b0e12", "#3a4048", sw=0.05),
                     text(3.0, -1.9, "KBL406", size=0.4, color=COL["ic_mark"])],
    })

    # -- more linear regulators ---------------------------------------------
    add(to220("ld1117-33", "LD1117-3.3 (TO-220)", "3.3 V LDO, 800 mA",
              ["GND", "OUT", "IN"], mark="1117",
              tags=["regulator", "ldo", "3v3"]))
    add(to92("lm78l05", "78L05", "5 V regulator, 100 mA",
             ["IN", "GND", "OUT"], category="power", designator="U", mark="78L05",
             tags=["regulator", "linear", "5v", "low power"]))
    add(to92("mcp1700-33", "MCP1700-3.3", "3.3 V LDO, 1.6 µA quiescent",
             ["GND", "OUT", "IN"], category="power", designator="U", mark="MCP1700",
             tags=["regulator", "ldo", "3v3", "low power", "battery"]))
    add(to92("lp2950-50", "LP2950-5.0", "5 V LDO, 100 mA",
             ["OUT", "GND", "IN"], category="power", designator="U", mark="LP2950",
             tags=["regulator", "ldo", "5v", "low dropout"]))

    # -- switching modules ---------------------------------------------------
    add(breakout("xl4015-module", "XL4015 buck module", "5 A adjustable step-down",
                 ["IN+", "IN-", "OUT-", "OUT+"], cols=20, rows=11, category="power",
                 pcb=COL["pcb_red"], pcb_edge="#4a0f18", mark="XL4015",
                 label_size=0.6, tags=["buck", "step-down", "switching", "dc-dc", "5a"]))
    add(breakout("sx1308-boost-module", "SX1308 boost", "2 A step-up, 2–24 V",
                 ["IN+", "IN-", "OUT-", "OUT+"], cols=9, rows=6, category="power",
                 pcb=COL["pcb_blue"], mark="SX1308",
                 tags=["boost", "step-up", "switching", "dc-dc"]))
    add(breakout("lm317-module", "LM317 module", "adjustable linear, 1.5 A",
                 ["IN+", "IN-", "OUT-", "OUT+"], cols=12, rows=10, category="power",
                 pcb=COL["pcb_green"], pcb_edge=COL["pcb_green_edge"], mark="LM317",
                 label_size=0.5, tags=["regulator", "linear", "adjustable", "module"]))
    add(breakout("tp4056-protected", "TP4056 + protection", "charger with DW01 + 8205",
                 ["IN+", "IN-", "BAT+", "BAT-", "OUT+", "OUT-"],
                 cols=10, rows=9, category="power", pcb=COL["pcb_blue"],
                 mark="TP4056 P", tags=["charger", "lithium", "lipo", "protection",
                                        "dw01", "18650"]))

    # Isolated DC-DC brick, DIP-4 outline.
    add({
        "id": "b0505s-dcdc", "name": "B0505S-1W", "subtitle": "isolated 5 V → 5 V, 1 W",
        "category": "power",
        "tags": ["dc-dc", "isolated", "converter", "5v", "1w"],
        "designator": "U",
        "footprint": {"cols": 4, "rows": 2},
        "pins": [pin(0, 0, "-VIN", 1, "gnd"), pin(0, 1, "+VIN", 2, "power"),
                 pin(3, 1, "-VOUT", 3, "gnd"), pin(3, 0, "+VOUT", 4, "power")],
        "body": {"x": -0.45, "y": -0.45, "w": 4.4, "h": 1.9, "rx": 0.1,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [line(0, 0, 0.4, 0, COL["tin"], 0.1), line(0, 1, 0.4, 1, COL["tin"], 0.1),
                   line(3, 0, 2.6, 0, COL["tin"], 0.1), line(3, 1, 2.6, 1, COL["tin"], 0.1)],
        "label": {"text": "B0505S", "x": 1.5, "y": 0.5, "size": 0.36,
                  "color": COL["ic_mark"]},
    })

    # Mains AC-DC brick with the AC pins at one end and the DC pins at the other.
    add({
        "id": "hlk-pm01", "name": "HLK-PM01", "subtitle": "230 V AC → 5 V DC, 3 W",
        "category": "power",
        "tags": ["ac-dc", "mains", "psu", "5v", "hi-link", "isolated"],
        "designator": "PS",
        "footprint": {"cols": 13, "rows": 4},
        "pins": [pin(0, 0, "AC-L", 1, "in"), pin(0, 3, "AC-N", 2, "in"),
                 pin(12, 3, "-VO", 3, "gnd"), pin(12, 0, "+VO", 4, "power")],
        "body": {"x": -0.6, "y": -0.6, "w": 14.2, "h": 4.2, "rx": 0.12,
                 "fill": "#e9edf1", "stroke": "#a9b0b8"},
        "shapes": [
            rect(0.4, 0.4, 11.2, 2.2, "#dfe4ea", "#a9b0b8", rx=0.08),
            text(6.0, 1.5, "HLK-PM01", size=0.62, color="#3a3f47"),
            text(1.6, 2.9, "AC IN", size=0.36, color="#8f2020"),
            text(10.6, 2.9, "5V DC", size=0.36, color="#1c4478"),
        ],
    })


# ===========================================================================
# Sensors
# ===========================================================================

def build_sensor():
    add(breakout("dht11", "DHT11", "temperature + humidity",
                 ["VCC", "DATA", "NC", "GND"], cols=4, rows=6, category="sensor",
                 pcb="#2e6fb7", pcb_edge="#1b4477", mark="DHT11",
                 tags=["temperature", "humidity", "1-wire"],
                 extra_shapes=[rect(0.1, 1.2, 2.8, 3.0, "#3f86d6", "#255a97", rx=0.12)]))
    add(breakout("dht22", "DHT22 / AM2302", "temperature + humidity",
                 ["VCC", "DATA", "NC", "GND"], cols=5, rows=7, category="sensor",
                 pcb="#dfe4ea", pcb_edge="#a9b0b8", mark="DHT22",
                 tags=["temperature", "humidity", "am2302", "1-wire"],
                 label_size=0.4,
                 extra_shapes=[rect(0.2, 1.4, 3.6, 3.8, "#eef1f5", "#b6bcc4", rx=0.12)]))
    add(to92("ds18b20", "DS18B20", "1-Wire temperature", ["GND", "DQ", "VDD"],
             category="sensor", designator="U", mark="18B20",
             tags=["temperature", "1-wire", "digital"]))
    add(to92("tmp36", "TMP36", "analog temperature", ["VCC", "VOUT", "GND"],
             category="sensor", designator="U", mark="TMP36",
             tags=["temperature", "analog"]))
    add(to92("a3144-hall", "A3144", "Hall effect switch", ["VCC", "GND", "OUT"],
             category="sensor", designator="U", mark="A3144",
             tags=["hall", "magnetic", "switch"]))
    add(breakout("bme280", "BME280", "pressure / temp / humidity",
                 ["VCC", "GND", "SCL", "SDA"], cols=4, rows=5, category="sensor",
                 pcb=COL["pcb_purple"], pcb_edge="#1c1029", mark="BME280",
                 tags=["i2c", "pressure", "humidity", "temperature", "barometer"]))
    add(breakout("bmp280", "BMP280", "pressure + temperature",
                 ["VCC", "GND", "SCL", "SDA"], cols=4, rows=5, category="sensor",
                 pcb=COL["pcb_purple"], pcb_edge="#1c1029", mark="BMP280",
                 tags=["i2c", "pressure", "barometer", "altimeter"]))
    add(breakout("mpu6050", "MPU-6050", "6-axis accel + gyro",
                 ["VCC", "GND", "SCL", "SDA", "XDA", "XCL", "AD0", "INT"],
                 cols=8, rows=6, category="sensor", pcb=COL["pcb_blue"],
                 mark="MPU-6050", tags=["imu", "accelerometer", "gyroscope", "i2c"]))
    add(breakout("adxl345", "ADXL345", "3-axis accelerometer",
                 ["GND", "VCC", "CS", "INT1", "INT2", "SDO", "SDA", "SCL"],
                 cols=8, rows=6, category="sensor", pcb=COL["pcb_purple"],
                 pcb_edge="#1c1029", mark="ADXL345",
                 tags=["accelerometer", "i2c", "spi"]))
    add(breakout("hc-sr04", "HC-SR04", "ultrasonic range finder",
                 ["VCC", "TRIG", "ECHO", "GND"], cols=18, rows=8, category="sensor",
                 pcb=COL["pcb_blue"], mark="HC-SR04",
                 tags=["ultrasonic", "distance", "range"], label_size=0.5,
                 extra_shapes=[circle(4.0, 4.0, 3.1, "#8d949c", "#5c6269", sw=0.08),
                               circle(13.0, 4.0, 3.1, "#8d949c", "#5c6269", sw=0.08),
                               circle(4.0, 4.0, 2.4, "#5c6269"),
                               circle(13.0, 4.0, 2.4, "#5c6269")]))
    add(breakout("hc-sr501", "HC-SR501 PIR", "motion detector",
                 ["VCC", "OUT", "GND"], cols=12, rows=12, category="sensor",
                 pcb=COL["pcb_green"], pcb_edge=COL["pcb_green_edge"], mark="PIR",
                 tags=["pir", "motion", "infrared"], label_size=0.5,
                 extra_shapes=[circle(5.5, 6.0, 4.6, "#e6e9ee", "#a8aeb6", sw=0.1),
                               circle(5.5, 6.0, 3.4, "#f2f4f7", "#b8bec6", sw=0.06)]))
    add(breakout("vl53l0x", "VL53L0X", "ToF laser distance",
                 ["VCC", "GND", "SCL", "SDA", "GPIO1", "XSHUT"],
                 cols=6, rows=5, category="sensor", pcb=COL["pcb_purple"],
                 pcb_edge="#1c1029", mark="VL53L0X",
                 tags=["tof", "laser", "distance", "i2c"]))
    add(breakout("ds3231-module", "DS3231 RTC", "precision I2C clock",
                 ["32K", "SQW", "SCL", "SDA", "VCC", "GND"],
                 cols=15, rows=8, category="sensor", pcb=COL["pcb_blue"],
                 mark="DS3231", tags=["rtc", "clock", "i2c", "eeprom"],
                 label_size=0.5,
                 extra_shapes=[circle(9.0, 4.5, 2.6, "#c9ced6", "#8d949c", sw=0.08),
                               text(9.0, 4.5, "CR2032", size=0.4, color="#5c6269")]))
    add(breakout("hx711-module", "HX711", "24-bit load-cell ADC",
                 ["GND", "DT", "SCK", "VCC"], cols=8, rows=7, category="sensor",
                 pcb=COL["pcb_red"], pcb_edge="#4a0f18", mark="HX711",
                 tags=["adc", "load cell", "strain gauge", "scale"]))
    add(breakout("mq-2", "MQ-2 gas sensor", "LPG / smoke / propane",
                 ["VCC", "GND", "DO", "AO"], cols=12, rows=10, category="sensor",
                 pcb=COL["pcb_blue"], mark="MQ-2", tags=["gas", "smoke", "analog"],
                 label_size=0.5,
                 extra_shapes=[circle(5.5, 5.5, 3.4, "#b8460f", "#7d2f0a", sw=0.1),
                               circle(5.5, 5.5, 2.6, "#d0d5db", "#8d949c", sw=0.08)]))
    add(breakout("acs712", "ACS712", "Hall current sensor",
                 ["VCC", "OUT", "GND"], cols=12, rows=8, category="sensor",
                 pcb=COL["pcb_blue"], mark="ACS712", tags=["current", "hall", "analog"],
                 label_size=0.5))
    add(breakout("soil-moisture", "Soil moisture", "capacitive / resistive probe",
                 ["VCC", "GND", "AOUT"], cols=4, rows=5, category="sensor",
                 pcb=COL["pcb_black"], mark="SOIL", tags=["soil", "moisture", "analog"]))
    add(breakout("ky-038-sound", "KY-038 sound", "microphone module",
                 ["AO", "GND", "VCC", "DO"], cols=10, rows=7, category="sensor",
                 pcb=COL["pcb_blue"], mark="SOUND", tags=["sound", "microphone", "analog"]))
    add(breakout("ir-obstacle", "IR obstacle sensor", "reflective detector",
                 ["VCC", "GND", "OUT"], cols=10, rows=6, category="sensor",
                 pcb=COL["pcb_blue"], mark="IR", tags=["infrared", "obstacle", "proximity"]))

    # Two-lead sensors.
    add({
        "id": "ldr-5mm", "name": "LDR 5 mm", "subtitle": "photoresistor GL5528",
        "category": "sensor", "tags": ["ldr", "light", "photoresistor", "analog"],
        "designator": "R",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0.5, -0.1, COL["lead"], 0.1),
            line(1, 0, 0.5, -0.1, COL["lead"], 0.1),
            circle(0.5, -0.4, 0.52, "#e8b96a", "#a8813c", sw=0.05),
            path("M -0.02 -0.4 m 0.12 0 q 0.16 -0.22 0.32 0 q 0.16 0.22 0.32 0 "
                 "q 0.16 -0.22 0.32 0", stroke="#5c4520", sw=0.07),
        ],
        "label": {"text": "LDR", "x": 0.5, "y": 0.42, "size": 0.28, "color": "#9fb0c0"},
    })
    add({
        "id": "ntc-10k", "name": "NTC 10 kΩ", "subtitle": "thermistor, B3950",
        "category": "sensor", "tags": ["thermistor", "ntc", "temperature", "analog"],
        "designator": "TH",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0.5, -0.1, COL["lead"], 0.1),
            line(1, 0, 0.5, -0.1, COL["lead"], 0.1),
            circle(0.5, -0.36, 0.4, "#1f2a35", "#0d1319", sw=0.05),
        ],
        "label": {"text": "NTC", "x": 0.5, "y": 0.42, "size": 0.28, "color": "#9fb0c0"},
    })
    add({
        "id": "reed-switch", "name": "Reed switch", "subtitle": "magnetic contact",
        "category": "sensor", "tags": ["reed", "magnetic", "switch"], "designator": "SW",
        "footprint": {"cols": 6, "rows": 1},
        "resize": {"axis": "cols", "min": 4, "max": 10},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(5, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 5, 0, COL["lead"], 0.09),
            {"type": "rect", "x": 1.2, "y": -0.28, "w": 2.6, "h": 0.56,
             "rx": 0.28, "fill": "#cfd8e2", "stroke": "#8d949c", "strokeWidth": 0.04,
             "opacity": 0.85},
            line(1.5, -0.06, 2.6, -0.06, COL["steel"], 0.07, "butt"),
            line(2.4, 0.06, 3.5, 0.06, COL["steel"], 0.07, "butt"),
        ],
    })

    # -- environment ---------------------------------------------------------
    add(breakout("aht20", "AHT20", "temperature + humidity, I2C",
                 ["VIN", "GND", "SCL", "SDA"], cols=6, rows=6, category="sensor",
                 pcb=COL["pcb_purple"], pcb_edge="#1c1029", mark="AHT20",
                 tags=["temperature", "humidity", "i2c", "asair"]))
    add(breakout("sht31", "SHT31", "±2 %RH, ±0.3 °C, I2C",
                 ["VIN", "GND", "SCL", "SDA", "ADR", "ALT"], cols=6, rows=5,
                 category="sensor", pcb=COL["pcb_purple"], pcb_edge="#1c1029",
                 mark="SHT31", tags=["temperature", "humidity", "i2c", "sensirion"]))
    add(breakout("bmp180", "BMP180", "barometric pressure, I2C",
                 ["VCC", "GND", "SCL", "SDA"], cols=5, rows=5, category="sensor",
                 pcb=COL["pcb_blue"], mark="BMP180",
                 tags=["pressure", "barometer", "altitude", "i2c", "bosch"]))
    add(to92("lm35", "LM35", "10 mV/°C analogue temperature",
             ["+VS", "OUT", "GND"], category="sensor", designator="U", mark="LM35",
             tags=["temperature", "analog", "linear"]))
    add(breakout("mlx90614", "MLX90614", "non-contact IR thermometer, I2C",
                 ["VIN", "GND", "SCL", "SDA"], cols=6, rows=8, category="sensor",
                 pcb=COL["pcb_purple"], pcb_edge="#1c1029", mark="MLX90614",
                 label_size=0.42, tags=["temperature", "infrared", "i2c", "contactless"],
                 extra_shapes=[circle(2.5, 4.5, 1.1, COL["steel"], "#6f767e", sw=0.06),
                               circle(2.5, 4.5, 0.55, "#14171a")]))
    add(breakout("max6675", "MAX6675", "K-type thermocouple to SPI",
                 ["GND", "VCC", "SCK", "CS", "SO"], cols=6, rows=8, category="sensor",
                 pcb=COL["pcb_red"], pcb_edge="#4a0f18", mark="MAX6675",
                 label_size=0.42, tags=["thermocouple", "temperature", "spi", "k-type"]))

    # -- light and colour -----------------------------------------------------
    add(breakout("bh1750", "BH1750", "digital lux meter, I2C",
                 ["VCC", "GND", "SCL", "SDA", "ADDR"], cols=5, rows=5,
                 category="sensor", pcb=COL["pcb_purple"], pcb_edge="#1c1029",
                 mark="BH1750", tags=["light", "lux", "ambient", "i2c", "rohm"]))
    add(breakout("tcs34725", "TCS34725", "RGB colour sensor, I2C",
                 ["VIN", "3V3", "GND", "SDA", "SCL", "INT", "LED"], cols=7, rows=7,
                 category="sensor", pcb=COL["pcb_black"], mark="TCS34725",
                 label_size=0.42, tags=["colour", "rgb", "light", "i2c"]))
    add(breakout("apds9960", "APDS-9960", "gesture, proximity, RGB",
                 ["VIN", "3V3", "GND", "SDA", "SCL", "INT"], cols=6, rows=6,
                 category="sensor", pcb=COL["pcb_black"], mark="APDS9960",
                 label_size=0.42, tags=["gesture", "proximity", "colour", "i2c"]))

    # -- motion and orientation ----------------------------------------------
    add(breakout("mpu9250", "MPU-9250", "9-axis IMU, I2C / SPI",
                 ["VCC", "GND", "SCL", "SDA", "EDA", "ECL", "AD0", "INT", "NCS", "FSYNC"],
                 cols=10, rows=6, category="sensor", pcb=COL["pcb_purple"],
                 pcb_edge="#1c1029", mark="MPU-9250", label_size=0.5,
                 tags=["imu", "gyro", "accelerometer", "magnetometer", "9-axis"]))
    add(breakout("bno055", "BNO055", "9-axis IMU with fusion",
                 ["VIN", "3VO", "GND", "SDA", "SCL", "RST", "INT", "ADR", "PS0", "PS1"],
                 cols=10, rows=7, category="sensor", pcb=COL["pcb_black"],
                 mark="BNO055", label_size=0.5,
                 tags=["imu", "fusion", "orientation", "quaternion", "bosch"]))
    add(breakout("qmc5883l", "QMC5883L", "3-axis magnetometer / compass",
                 ["VCC", "GND", "SCL", "SDA", "DRDY"], cols=5, rows=5,
                 category="sensor", pcb=COL["pcb_purple"], pcb_edge="#1c1029",
                 mark="QMC5883", label_size=0.4,
                 tags=["compass", "magnetometer", "heading", "i2c"]))
    add(breakout("hc-sr312", "HC-SR312 mini PIR", "3.3 V motion detector",
                 ["GND", "OUT", "VCC"], cols=4, rows=5, category="sensor",
                 pcb=COL["pcb_green"], pcb_edge=COL["pcb_green_edge"], mark="SR312",
                 tags=["pir", "motion", "presence", "infrared"],
                 extra_shapes=[circle(1.5, 2.6, 1.5, "#e9edf1", "#a9b0b8", sw=0.06,
                                      opacity=0.9)]))
    add({
        "id": "tilt-sw520d", "name": "Tilt switch SW-520D", "subtitle": "ball tilt, 2 pin",
        "category": "sensor", "tags": ["tilt", "switch", "orientation", "ball"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0, -0.5, COL["lead"], 0.1),
            line(2, 0, 2, -0.5, COL["lead"], 0.1),
            rect(-0.35, -1.9, 2.7, 1.4, COL["tin"], "#7f868e", rx=0.65),
            circle(1.4, -1.2, 0.42, "#4c5359", "#22262c", sw=0.05),
        ],
        "label": {"text": "TILT", "x": 1.0, "y": 0.44, "size": 0.3, "color": "#9fb0c0"},
    })
    add({
        "id": "vibration-sw18010", "name": "Vibration switch SW-18010P",
        "subtitle": "spring vibration sensor",
        "category": "sensor", "tags": ["vibration", "shock", "switch", "spring"],
        "designator": "SW",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0, -0.6, COL["lead"], 0.1),
            line(1, 0, 1, -0.6, COL["lead"], 0.1),
            rect(-0.28, -2.4, 1.56, 1.8, COL["tin"], "#7f868e", rx=0.7),
            line(0.5, -2.2, 0.5, -0.8, "#6f767e", 0.08),
        ],
        "label": {"text": "VIB", "x": 0.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    })

    # -- gas, water, flame ----------------------------------------------------
    for mid, name, gas in (("mq-135", "MQ-135", "air quality / NH3 / NOx"),
                           ("mq-7", "MQ-7", "carbon monoxide")):
        add(breakout(mid, f"{name} gas sensor", gas,
                     ["AO", "DO", "GND", "VCC"], cols=8, rows=12, category="sensor",
                     pcb=COL["pcb_blue"], mark=name, label_size=0.6,
                     tags=["gas", "air", "analog", mid],
                     extra_shapes=[circle(3.5, 6.0, 2.4, COL["steel"], "#6f767e", sw=0.08),
                                   circle(3.5, 6.0, 1.7, "#7f868e", "#5c6269", sw=0.05)]))
    add(breakout("flame-sensor", "Flame sensor", "IR photodiode, 760–1100 nm",
                 ["AO", "GND", "VCC", "DO"], cols=6, rows=8, category="sensor",
                 pcb=COL["pcb_blue"], mark="FLAME",
                 tags=["flame", "fire", "infrared", "photodiode"],
                 extra_shapes=[circle(2.5, 5.4, 0.62, "#2b3a6b", "#16204a", sw=0.05)]))
    add(breakout("rain-sensor", "Rain sensor board", "comparator + interdigital plate",
                 ["AO", "DO", "GND", "VCC"], cols=6, rows=8, category="sensor",
                 pcb=COL["pcb_blue"], mark="RAIN",
                 tags=["rain", "water", "moisture", "drop"]))
    add(breakout("water-level-sensor", "Water level sensor", "resistive depth strip",
                 ["S", "+", "-"], cols=4, rows=16, category="sensor",
                 pcb=COL["pcb_blue"], mark="LEVEL", label_size=0.5,
                 tags=["water", "level", "depth", "analog"],
                 extra_shapes=[rect(0.4, 4.0, 2.2, 11.0, COL["gold"], "#8a6f1a",
                                    rx=0.1, opacity=0.85)]))
    add(breakout("ttp223-touch", "TTP223 touch pad", "capacitive touch button",
                 ["VCC", "GND", "IO"], cols=5, rows=6, category="sensor",
                 pcb=COL["pcb_blue"], mark="TTP223",
                 tags=["touch", "capacitive", "button", "pad"],
                 extra_shapes=[rect(0.6, 2.6, 3.0, 2.0, COL["gold"], "#8a6f1a", rx=0.14)]))


# ===========================================================================
# Displays
# ===========================================================================

def build_display():
    add(breakout("ssd1306-096-i2c", "OLED 0.96\" I2C", "SSD1306, 128×64",
                 ["GND", "VCC", "SCL", "SDA"], cols=11, rows=10, category="display",
                 pcb=COL["pcb_blue"], mark="OLED 0.96", label_size=0.45,
                 tags=["oled", "ssd1306", "i2c", "display"],
                 extra_shapes=[rect(1.0, 2.2, 8.0, 5.0, COL["display_glass"],
                                    "#2a3038", rx=0.12),
                               rect(1.4, 2.6, 7.2, 4.2, "#0e131a", None)]))
    add(breakout("ssd1306-096-spi", "OLED 0.96\" SPI", "SSD1306, 7-pin",
                 ["GND", "VCC", "D0/SCK", "D1/MOSI", "RES", "DC", "CS"],
                 cols=11, rows=10, category="display", pcb=COL["pcb_blue"],
                 mark="OLED SPI", label_size=0.45,
                 tags=["oled", "ssd1306", "spi", "display"],
                 extra_shapes=[rect(1.0, 2.2, 8.0, 5.0, COL["display_glass"],
                                    "#2a3038", rx=0.12)]))
    add(breakout("sh1106-13-i2c", "OLED 1.3\" I2C", "SH1106, 128×64",
                 ["GND", "VCC", "SCL", "SDA"], cols=14, rows=13, category="display",
                 pcb=COL["pcb_blue"], mark="OLED 1.3", label_size=0.5,
                 tags=["oled", "sh1106", "i2c", "display"],
                 extra_shapes=[rect(1.2, 2.6, 11.0, 7.0, COL["display_glass"],
                                    "#2a3038", rx=0.14)]))
    add(breakout("lcd1602", "LCD 16×2", "HD44780 character LCD",
                 ["VSS", "VDD", "V0", "RS", "RW", "E", "D0", "D1", "D2", "D3",
                  "D4", "D5", "D6", "D7", "A", "K"],
                 cols=32, rows=14, category="display", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="LCD 1602", label_size=0.7,
                 tags=["lcd", "hd44780", "character", "1602"],
                 extra_shapes=[rect(3.0, 4.0, 26.0, 7.5, "#2f6b4f", "#1d4433", rx=0.15),
                               rect(4.2, 4.9, 23.6, 5.7, "#5fbf8f", "#3d8f68", rx=0.1)]))
    add(breakout("lcd2004", "LCD 20×4", "HD44780 character LCD",
                 ["VSS", "VDD", "V0", "RS", "RW", "E", "D0", "D1", "D2", "D3",
                  "D4", "D5", "D6", "D7", "A", "K"],
                 cols=38, rows=23, category="display", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="LCD 2004", label_size=0.8,
                 tags=["lcd", "hd44780", "character", "2004"],
                 extra_shapes=[rect(3.0, 5.0, 32.0, 13.0, "#2f6b4f", "#1d4433", rx=0.15),
                               rect(4.5, 6.2, 29.0, 10.6, "#5fbf8f", "#3d8f68", rx=0.1)]))
    add(breakout("i2c-lcd-backpack", "I2C LCD backpack", "PCF8574 adapter",
                 ["GND", "VCC", "SDA", "SCL"], cols=6, rows=5, category="display",
                 pcb=COL["pcb_green"], pcb_edge=COL["pcb_green_edge"], mark="I2C LCD",
                 tags=["i2c", "lcd", "pcf8574", "backpack"]))
    add(breakout("tm1637-4digit", "TM1637 4-digit", "7-segment display module",
                 ["VCC", "GND", "DIO", "CLK"], cols=17, rows=8, category="display",
                 pcb=COL["pcb_black"], mark="TM1637", label_size=0.55,
                 tags=["7-segment", "display", "tm1637", "digits"],
                 extra_shapes=[rect(1.5, 2.0, 14.0, 4.5, "#14171a", "#2a3038", rx=0.12)]
                              + [text(3.4 + i * 3.2, 4.3, "8", size=1.5, color="#5c1a1a")
                                 for i in range(4)]))
    add(breakout("max7219-matrix", "MAX7219 8×8 matrix", "LED matrix module",
                 ["VCC", "GND", "DIN", "CS", "CLK"], cols=13, rows=13,
                 category="display", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="MAX7219", label_size=0.5,
                 tags=["led matrix", "max7219", "spi", "8x8"],
                 extra_shapes=[rect(1.2, 2.4, 10.6, 9.4, "#14171a", "#2a3038", rx=0.12)]
                              + [circle(2.2 + c * 1.2, 3.4 + r * 1.2, 0.32, "#5c1a1a")
                                 for r in range(8) for c in range(8)]))
    add(breakout("nokia5110", "Nokia 5110 LCD", "PCD8544, 84×48",
                 ["RST", "CE", "DC", "DIN", "CLK", "VCC", "BL", "GND"],
                 cols=17, rows=15, category="display", pcb=COL["pcb_red"],
                 pcb_edge="#4a0f18", mark="5110", label_size=0.55,
                 tags=["lcd", "pcd8544", "nokia", "spi"],
                 extra_shapes=[rect(1.5, 3.0, 14.0, 9.0, "#8f9a7a", "#5e6650", rx=0.12)]))
    add(breakout("st7735-18-tft", "TFT 1.8\" ST7735", "160×128 SPI colour",
                 ["GND", "VCC", "SCK", "SDA", "RST", "DC", "CS", "BL"],
                 cols=14, rows=17, category="display", pcb=COL["pcb_black"],
                 mark="ST7735", label_size=0.5,
                 tags=["tft", "st7735", "spi", "colour", "display"],
                 extra_shapes=[rect(1.2, 2.6, 11.6, 11.0, COL["display_glass"],
                                    "#2a3038", rx=0.12)]))
    add(breakout("ili9341-24-tft", "TFT 2.4\" ILI9341", "320×240 SPI + touch",
                 ["VCC", "GND", "CS", "RST", "DC", "SDI", "SCK", "LED", "SDO",
                  "T_CLK", "T_CS", "T_DIN", "T_DO", "T_IRQ"],
                 cols=26, rows=22, category="display", pcb=COL["pcb_black"],
                 mark="ILI9341", label_size=0.7,
                 tags=["tft", "ili9341", "spi", "touch", "display"],
                 extra_shapes=[rect(2.0, 3.0, 22.0, 16.0, COL["display_glass"],
                                    "#2a3038", rx=0.14)]))

    # Single 7-segment digit: two rows of five pins, 0.6" apart.
    add({
        "id": "7seg-1digit", "name": "7-segment digit", "subtitle": "0.56\" common cathode",
        "category": "display", "tags": ["7-segment", "led", "digit", "display"],
        "designator": "DS",
        "footprint": {"cols": 6, "rows": 5},
        "pins": [pin(0, 0, "E", 1, "io"), pin(0, 1, "D", 2, "io"),
                 pin(0, 2, "CC", 3, "gnd"), pin(0, 3, "C", 4, "io"),
                 pin(0, 4, "DP", 5, "io"),
                 pin(5, 0, "G", 10, "io"), pin(5, 1, "F", 9, "io"),
                 pin(5, 2, "CC", 8, "gnd"), pin(5, 3, "A", 7, "io"),
                 pin(5, 4, "B", 6, "io")],
        "body": {"x": -0.4, "y": -0.4, "w": 5.8, "h": 4.8, "rx": 0.1,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": [
            rect(1.3, 0.3, 2.4, 0.28, "#5c1a1a", None, rx=0.14),           # a
            rect(3.55, 0.5, 0.28, 1.5, "#5c1a1a", None, rx=0.14),          # b
            rect(3.55, 2.2, 0.28, 1.5, "#5c1a1a", None, rx=0.14),          # c
            rect(1.3, 3.65, 2.4, 0.28, "#5c1a1a", None, rx=0.14),          # d
            rect(1.15, 2.2, 0.28, 1.5, "#5c1a1a", None, rx=0.14),          # e
            rect(1.15, 0.5, 0.28, 1.5, "#5c1a1a", None, rx=0.14),          # f
            rect(1.3, 1.98, 2.4, 0.28, "#5c1a1a", None, rx=0.14),          # g
            circle(4.2, 3.8, 0.2, "#5c1a1a"),                              # dp
        ],
    })
    add({
        "id": "ws2812b-module", "name": "WS2812B NeoPixel", "subtitle": "addressable RGB LED",
        "category": "display", "tags": ["ws2812b", "neopixel", "rgb", "addressable"],
        "designator": "D",
        "footprint": {"cols": 4, "rows": 3},
        "pins": [pin(0, 0, "VCC", 1, "power"), pin(1, 0, "DIN", 2, "in"),
                 pin(2, 0, "DOUT", 3, "out"), pin(3, 0, "GND", 4, "gnd")],
        "body": {"x": -0.4, "y": -0.4, "w": 4.8, "h": 2.8, "rx": 0.14,
                 "fill": COL["pcb_black"], "stroke": COL["ic_edge"]},
        "shapes": [
            rect(-0.32, -0.32, 3.64, 0.64, COL["plastic_black"], COL["ic_edge"], rx=0.08),
            rect(0.9, 0.9, 1.8, 1.2, "#f0f2f5", "#b8bec6", rx=0.1),
            circle(1.8, 1.5, 0.42, "#3a3f47", None),
            circle(1.62, 1.36, 0.14, "#d84040"), circle(1.98, 1.36, 0.14, "#40d868"),
            circle(1.8, 1.66, 0.14, "#4070d8"),
        ],
        "label": {"text": "WS2812B", "x": 1.8, "y": 2.2, "size": 0.3, "color": COL["silk"]},
    })

    # -- multi-digit 7-segment ----------------------------------------------
    # Segment artwork for one digit whose top-left corner sits at (ox, oy).
    def seg_digit(ox, oy, w=2.4, h=3.6, t=0.28, off="#5c1a1a"):
        return [
            rect(ox + t / 2, oy, w, t, off, None, rx=t / 2),                       # a
            rect(ox + w + t / 2, oy + t / 2, t, h / 2, off, None, rx=t / 2),       # b
            rect(ox + w + t / 2, oy + h / 2 + t, t, h / 2, off, None, rx=t / 2),   # c
            rect(ox + t / 2, oy + h + t, w, t, off, None, rx=t / 2),               # d
            rect(ox, oy + h / 2 + t, t, h / 2, off, None, rx=t / 2),               # e
            rect(ox, oy + t / 2, t, h / 2, off, None, rx=t / 2),                   # f
            rect(ox + t / 2, oy + h / 2 + t / 2, w, t, off, None, rx=t / 2),       # g
            circle(ox + w + 1.0, oy + h + t, 0.2, off),                            # dp
        ]

    add({
        "id": "7seg-2digit", "name": "7-segment, 2 digits",
        "subtitle": "5241AS, 0.56 in common cathode",
        "category": "display", "tags": ["7-segment", "led", "digits", "5241as", "display"],
        "designator": "DS",
        "footprint": {"cols": 5, "rows": 7},
        # Bottom row is pins 1-5 left to right; top row is 10-6 left to right.
        "pins": [pin(0, 6, "E", 1, "io"), pin(1, 6, "D", 2, "io"),
                 pin(2, 6, "DP", 3, "io"), pin(3, 6, "C", 4, "io"),
                 pin(4, 6, "G", 5, "io"),
                 pin(0, 0, "CC1", 10, "gnd"), pin(1, 0, "F", 9, "io"),
                 pin(2, 0, "A", 8, "io"), pin(3, 0, "CC2", 7, "gnd"),
                 pin(4, 0, "B", 6, "io")],
        "body": {"x": -0.9, "y": -0.5, "w": 6.8, "h": 7.0, "rx": 0.1,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": seg_digit(-0.2, 1.1) + seg_digit(2.9, 1.1),
    })
    add({
        "id": "7seg-4digit", "name": "7-segment, 4 digits",
        "subtitle": "3461AS, multiplexed common cathode",
        "category": "display", "tags": ["7-segment", "led", "digits", "3461as",
                                        "multiplexed", "display"],
        "designator": "DS",
        "footprint": {"cols": 6, "rows": 7},
        # Bottom row is pins 1-6 left to right; top row is 12-7 left to right.
        "pins": [pin(0, 6, "E", 1, "io"), pin(1, 6, "D", 2, "io"),
                 pin(2, 6, "DP", 3, "io"), pin(3, 6, "C", 4, "io"),
                 pin(4, 6, "G", 5, "io"), pin(5, 6, "D4", 6, "gnd"),
                 pin(0, 0, "D1", 12, "gnd"), pin(1, 0, "A", 11, "io"),
                 pin(2, 0, "F", 10, "io"), pin(3, 0, "D2", 9, "gnd"),
                 pin(4, 0, "D3", 8, "gnd"), pin(5, 0, "B", 7, "io")],
        "body": {"x": -2.9, "y": -0.5, "w": 11.8, "h": 7.0, "rx": 0.1,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": (seg_digit(-2.3, 1.1, w=1.7, h=3.4)
                   + seg_digit(0.1, 1.1, w=1.7, h=3.4)
                   + seg_digit(3.4, 1.1, w=1.7, h=3.4)
                   + seg_digit(5.8, 1.1, w=1.7, h=3.4)
                   + [circle(2.9, 2.2, 0.18, "#5c1a1a"),
                      circle(2.9, 3.6, 0.18, "#5c1a1a")]),   # colon
    })
    add({
        "id": "led-bar-10seg", "name": "LED bar graph, 10 segment",
        "subtitle": "20-pin, 0.4 in rows",
        "category": "display", "tags": ["bar graph", "led", "level", "vu", "display"],
        "designator": "DS",
        "footprint": {"cols": 5, "rows": 10},
        "pins": ([pin(0, i, f"A{i + 1}", i + 1, "power") for i in range(10)]
                 + [pin(4, i, f"K{i + 1}", 20 - i, "gnd") for i in range(10)]),
        "body": {"x": -0.3, "y": -0.5, "w": 4.6, "h": 10.0, "rx": 0.1,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": [rect(0.6, i - 0.22, 2.8, 0.44,
                        "#5c1a1a" if i > 2 else "#1a4a2a", None, rx=0.08)
                   for i in range(10)],
    })

    # -- more panels ---------------------------------------------------------
    add(breakout("ssd1306-091-i2c", "OLED 0.91 in I2C", "SSD1306, 128 x 32",
                 ["GND", "VCC", "SCL", "SDA"], cols=9, rows=6, category="display",
                 pcb=COL["pcb_blue"], mark="OLED 0.91", label_size=0.4,
                 tags=["oled", "ssd1306", "i2c", "display", "128x32"],
                 extra_shapes=[rect(0.8, 1.8, 6.6, 2.4, COL["display_glass"],
                                    "#2a3038", rx=0.1)]))
    add(breakout("oled-242-spi", "OLED 2.42 in SPI", "SSD1309, 128 x 64",
                 ["GND", "VCC", "SCK", "SDA", "RES", "DC", "CS"],
                 cols=14, rows=11, category="display", pcb=COL["pcb_black"],
                 mark="OLED 2.42", label_size=0.5,
                 tags=["oled", "ssd1309", "spi", "display", "large"],
                 extra_shapes=[rect(1.0, 2.4, 11.2, 6.4, COL["display_glass"],
                                    "#2a3038", rx=0.12)]))
    add(breakout("epaper-154", "e-Paper 1.54 in", "200 x 200, SPI, partial refresh",
                 ["VCC", "GND", "DIN", "CLK", "CS", "DC", "RST", "BUSY"],
                 cols=14, rows=18, category="display", pcb=COL["pcb_black"],
                 mark="E-PAPER", label_size=0.5,
                 tags=["epaper", "eink", "spi", "display", "low power"],
                 extra_shapes=[rect(1.0, 3.0, 11.4, 11.4, "#e9edf1", "#a9b0b8", rx=0.1)]))
    add(breakout("tm1638-module", "TM1638 key + display", "8 digits, 8 keys, 8 LEDs",
                 ["VCC", "GND", "STB", "CLK", "DIO"], cols=20, rows=8,
                 category="display", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="TM1638", label_size=0.55,
                 tags=["7-segment", "keypad", "tm1638", "display", "keys"],
                 extra_shapes=[rect(1.0, 1.4, 17.4, 2.4, "#14171a", "#2a3038", rx=0.1)]
                              + [circle(1.8 + i * 2.2, 5.6, 0.6, "#3a3f47", "#22262c",
                                        sw=0.05) for i in range(8)]))
    add(breakout("ht16k33-backpack", "HT16K33 backpack", "I2C 7-seg / matrix driver",
                 ["VCC", "GND", "SDA", "SCL"], cols=8, rows=7, category="display",
                 pcb=COL["pcb_black"], mark="HT16K33", label_size=0.42,
                 tags=["i2c", "driver", "backpack", "7-segment", "matrix"]))
    add(breakout("ws2812b-stick-8", "WS2812B stick, 8 LED", "addressable RGB bar",
                 ["5V", "DIN", "GND"], cols=20, rows=4, category="display",
                 pcb=COL["pcb_black"], mark="8 x WS2812B", label_size=0.45,
                 tags=["ws2812b", "neopixel", "rgb", "addressable", "strip"],
                 extra_shapes=[rect(2.0 + i * 2.2, 1.2, 1.5, 1.5, "#f0f2f5",
                                    "#b8bec6", rx=0.1) for i in range(8)]))
    add({
        "id": "matrix-8x8-1088as", "name": "LED matrix 8x8 (1088AS)",
        "subtitle": "bare 16-pin dot matrix",
        "category": "display", "tags": ["led matrix", "8x8", "1088as", "dot matrix"],
        "designator": "DS",
        "footprint": {"cols": 12, "rows": 12},
        "pins": ([pin(i + 2, 0, str(16 - i), 16 - i, "io") for i in range(8)]
                 + [pin(i + 2, 11, str(i + 1), i + 1, "io") for i in range(8)]),
        "body": {"x": -0.5, "y": -0.5, "w": 12.0, "h": 12.0, "rx": 0.1,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": [circle(1.9 + c * 1.1, 1.9 + r * 1.1, 0.34, "#5c1a1a")
                   for r in range(8) for c in range(8)],
    })


# ===========================================================================
# Passives
# ===========================================================================

# The E12 series from 1 Ω to 10 MΩ, plus 300 Ω which is sold everywhere even
# though it is E24.  Colour bands are computed from the value, so extending this
# list is all it takes to add a resistor.
RESISTOR_VALUES = [
    1, 2.2, 4.7, 5.6, 8.2, 10, 15, 22, 33, 47, 68,
    100, 120, 150, 180, 220, 270, 300, 330, 390, 470, 560, 680, 820,
    1000, 1200, 1500, 1800, 2200, 2700, 3300, 3900, 4700, 5600, 6800, 8200,
    10000, 12000, 15000, 18000, 22000, 27000, 33000, 39000, 47000, 56000,
    68000, 82000,
    100000, 120000, 150000, 180000, 220000, 270000, 330000, 470000, 680000,
    1000000, 1500000, 2200000, 4700000, 10000000,
]

ELECTROLYTICS = [
    (1, 50, 2, 2), (2.2, 50, 2, 2), (4.7, 50, 2, 2), (10, 25, 2, 2),
    (22, 25, 2, 2), (33, 16, 2, 2), (47, 25, 2, 2), (100, 16, 3, 2),
    (100, 50, 3, 2), (220, 16, 3, 2), (330, 25, 3, 2), (470, 25, 4, 2),
    (1000, 16, 4, 2), (1000, 35, 5, 3), (2200, 16, 5, 3), (3300, 16, 5, 3),
]

CERAMIC_DISC = [0.0000047, 0.00001, 0.000015, 0.000022, 0.000033, 0.000047,
                0.000068, 0.0001, 0.00015, 0.00022, 0.00033, 0.00047, 0.00068,
                0.001, 0.0015, 0.0022, 0.0033, 0.0047, 0.0068, 0.01, 0.015,
                0.022, 0.033, 0.047, 0.068, 0.1, 0.15, 0.22, 0.33, 0.47]
MLCC = [0.01, 0.1, 1.0, 4.7, 10.0, 22.0]


def build_passive():
    for v in RESISTOR_VALUES:
        add(axial_resistor(v))
    for uf, volts, dia, span in ELECTROLYTICS:
        add(electrolytic(uf, volts, dia, span))
    for v in CERAMIC_DISC:
        add(ceramic_cap(v, span=2, kind="disc"))
    for v in MLCC:
        m = ceramic_cap(v, span=2, kind="mlcc")
        m["id"] = m["id"]  # already distinct via 'mlcc' prefix
        add(m)

    # Film (polyester box) capacitors — the boxy blue ones.
    for slug, lbl, code in (("100nf", "100nF", "104"), ("220nf", "220nF", "224"),
                            ("470nf", "470nF", "474"), ("1uf", "1µF", "105")):
        add({
            "id": f"cap-film-{slug}", "name": f"Cap {lbl} film",
            "subtitle": "polyester box, 5 mm",
            "category": "passive",
            "tags": ["capacitor", "film", "polyester", slug, code],
            "designator": "C",
            "footprint": {"cols": 3, "rows": 1},
            "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
            "shapes": [
                line(0, 0, 0.4, -0.1, COL["lead"], 0.09),
                line(2, 0, 1.6, -0.1, COL["lead"], 0.09),
                rect(0.15, -0.95, 1.7, 0.85, COL["film"], "#1d3560", rx=0.1),
                text(1.0, -0.52, code, size=0.3, color="#d6e0f0"),
            ],
            "label": {"text": lbl, "x": 1.0, "y": 0.42, "size": 0.28, "color": "#9fb0c0"},
        })

    # Tantalum bead — polarised, marked on the PLUS lead unlike an electrolytic.
    for slug, lbl, volts in (("1uf", "1µF", 35), ("10uf", "10µF", 16),
                             ("100uf", "100µF", 16)):
        add({
            "id": f"cap-tant-{slug}", "name": f"Cap {lbl} tantalum",
            "subtitle": f"bead, {volts} V, polarised",
            "category": "passive",
            "tags": ["capacitor", "tantalum", "polarised", slug],
            "designator": "C",
            "footprint": {"cols": 2, "rows": 1},
            "pins": [pin(0, 0, "+", 1, "power"), pin(1, 0, "-", 2, "gnd")],
            "shapes": [
                line(0, 0, 0.5, -0.15, COL["lead"], 0.09),
                line(1, 0, 0.5, -0.15, COL["lead"], 0.09),
                path("M 0.5 -1.5 A 0.62 0.62 0 0 1 0.5 -0.26 Z", fill="#d8a63a",
                     stroke="#a87c20", sw=0.04),
                path("M 0.5 -1.5 A 0.62 0.62 0 0 0 0.5 -0.26 Z", fill="#e8bb56",
                     stroke="#a87c20", sw=0.04),
                text(0.24, -0.78, "+", size=0.34, color="#5c4410"),
            ],
            "label": {"text": lbl, "x": 0.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
        })

    # Trimmer potentiometer
    for val, lbl in ((1000, "1k"), (5000, "5k"), (10000, "10k"), (20000, "20k"),
                     (50000, "50k"), (100000, "100k"), (200000, "200k"),
                     (500000, "500k")):
        add({
            "id": f"trimpot-{lbl}", "name": f"Trimmer {lbl}Ω",
            "subtitle": "3386 style, top adjust",
            "category": "passive", "tags": ["potentiometer", "trimmer", "variable", lbl],
            "designator": "RV",
            "footprint": {"cols": 3, "rows": 1},
            "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "W", 2, "signal"),
                     pin(2, 0, "3", 3, "signal")],
            "body": {"x": -0.35, "y": -1.4, "w": 2.7, "h": 1.05, "rx": 0.08,
                     "fill": "#2f6bb5", "stroke": "#1c4478"},
            "shapes": [
                line(0, 0, 0, -0.35, COL["tin"], 0.1),
                line(1, 0, 1, -0.35, COL["tin"], 0.1),
                line(2, 0, 2, -0.35, COL["tin"], 0.1),
                circle(1.0, -0.88, 0.34, "#e8e2c8", "#a89f7c", sw=0.05),
                line(0.76, -0.88, 1.24, -0.88, "#5c5540", 0.09, "butt"),
                text(1.0, -1.62, lbl, size=0.3, color="#9fb0c0"),
            ],
        })

    # Panel potentiometer, 5 mm pin pitch
    for slug, disp in (("1k", "1 k"), ("10k", "10 k"), ("50k", "50 k"),
                       ("100k", "100 k"), ("500k", "500 k")):
        add({
            "id": f"pot-panel-{slug}", "name": f"Potentiometer {disp}Ω",
            "subtitle": "panel mount, 6 mm shaft",
            "category": "passive",
            "tags": ["potentiometer", "panel", "variable", slug],
            "designator": "RV",
            "footprint": {"cols": 5, "rows": 1},
            "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "W", 2, "signal"),
                     pin(4, 0, "3", 3, "signal")],
            "shapes": [
                line(0, 0, 0, -0.5, COL["tin"], 0.11),
                line(2, 0, 2, -0.5, COL["tin"], 0.11),
                line(4, 0, 4, -0.5, COL["tin"], 0.11),
                circle(2.0, -2.4, 1.95, "#b9c0c8", "#7f868e", sw=0.06),
                rect(-0.2, -0.9, 4.4, 0.45, "#8d949c", "#5c6269", rx=0.06),
                circle(2.0, -2.4, 0.55, "#3a3f47", "#22262c", sw=0.05),
                line(2.0, -2.4, 2.0, -3.9, "#c9ced6", 0.12),
            ],
            "label": {"text": slug, "x": 2.0, "y": 0.45, "size": 0.3, "color": "#9fb0c0"},
        })

    # Inductors
    for uh, lbl in ((10, "10µH"), (22, "22µH"), (47, "47µH"), (100, "100µH"),
                    (220, "220µH"), (470, "470µH"), (1000, "1mH")):
        add({
            "id": f"inductor-{uh}uh", "name": f"Inductor {lbl}",
            "subtitle": "axial choke",
            "category": "passive", "tags": ["inductor", "choke", "coil", f"{uh}uh"],
            "designator": "L",
            "footprint": {"cols": 3, "rows": 1},
            "resize": {"axis": "cols", "min": 3, "max": 8},
            "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
            "shapes": [
                line(0, 0, 0.55, 0, COL["lead"], 0.1),
                line(2, 0, 1.45, 0, COL["lead"], 0.1),
                rect(0.5, -0.3, 1.0, 0.6, "#3f3128", "#241a14", rx=0.26),
                rect(0.62, -0.28, 0.1, 0.56, "#e8c72c"),
                rect(0.82, -0.28, 0.1, 0.56, "#14171a"),
                rect(1.02, -0.28, 0.1, 0.56, "#6b4a2b"),
            ],
            "label": {"text": lbl, "x": 1.0, "y": -0.52, "size": 0.28, "color": "#9fb0c0"},
        })

    # Crystals
    for mid, name, lbl, span in (("crystal-4mhz", "Crystal 4 MHz", "4.000", 2),
                                 ("crystal-8mhz", "Crystal 8 MHz", "8.000", 2),
                                 ("crystal-11-0592mhz", "Crystal 11.0592 MHz",
                                  "11.0592", 2),
                                 ("crystal-12mhz", "Crystal 12 MHz", "12.000", 2),
                                 ("crystal-16mhz", "Crystal 16 MHz", "16.000", 2),
                                 ("crystal-20mhz", "Crystal 20 MHz", "20.000", 2),
                                 ("crystal-25mhz", "Crystal 25 MHz", "25.000", 2)):
        add({
            "id": mid, "name": name, "subtitle": "HC-49S low profile",
            "category": "passive", "tags": ["crystal", "oscillator", "clock", lbl],
            "designator": "Y",
            "footprint": {"cols": span, "rows": 1},
            "pins": [pin(0, 0, "1", 1, "signal"), pin(span - 1, 0, "2", 2, "signal")],
            "shapes": [
                line(0, 0, 0, -0.4, COL["tin"], 0.1),
                line(span - 1, 0, span - 1, -0.4, COL["tin"], 0.1),
                rect(-0.45, -1.45, (span - 1) + 0.9, 1.05, COL["crystal"], "#7f868e",
                     rx=0.45),
                text((span - 1) / 2, -0.92, lbl, size=0.26, color="#3a3f47"),
            ],
        })
    add({
        "id": "crystal-32k", "name": "Crystal 32.768 kHz", "subtitle": "cylindrical, RTC",
        "category": "passive", "tags": ["crystal", "rtc", "32768", "clock"],
        "designator": "Y",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0.5, -0.15, COL["lead"], 0.09),
            line(1, 0, 0.5, -0.15, COL["lead"], 0.09),
            rect(0.32, -1.35, 0.36, 1.15, COL["crystal"], "#7f868e", rx=0.18),
        ],
        "label": {"text": "32k", "x": 0.5, "y": 0.42, "size": 0.26, "color": "#9fb0c0"},
    })

    # -- protection & filtering ----------------------------------------------
    add({
        "id": "ferrite-bead", "name": "Ferrite bead", "subtitle": "axial EMI choke",
        "category": "passive", "tags": ["ferrite", "bead", "emi", "filter", "choke"],
        "designator": "FB",
        "footprint": {"cols": 3, "rows": 1},
        "resize": {"axis": "cols", "min": 2, "max": 8},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0.7, 0, COL["lead"], 0.1),
            line(2, 0, 1.3, 0, COL["lead"], 0.1),
            rect(0.65, -0.32, 0.7, 0.64, "#3a3f47", "#1a1d22", rx=0.2),
        ],
        "label": {"text": "FB", "x": 1.0, "y": -0.55, "size": 0.28, "color": "#9fb0c0"},
    })
    add({
        "id": "mov-14d471k", "name": "Varistor 14D471K", "subtitle": "MOV, 470 V clamp",
        "category": "passive", "tags": ["varistor", "mov", "surge", "protection", "mains"],
        "designator": "RV",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 1.0, -0.25, COL["lead"], 0.1),
            line(2, 0, 1.0, -0.25, COL["lead"], 0.1),
            circle(1.0, -1.15, 1.05, "#2f6bb5", "#1c4478", sw=0.06),
            text(1.0, -1.05, "14D", size=0.4, color="#dce6f2"),
        ],
        "label": {"text": "MOV", "x": 1.0, "y": 0.42, "size": 0.28, "color": "#9fb0c0"},
    })
    add({
        "id": "ptc-fuse-500ma", "name": "PTC resettable fuse 500 mA",
        "subtitle": "polyfuse, radial",
        "category": "passive", "tags": ["fuse", "ptc", "polyfuse", "resettable",
                                        "protection"],
        "designator": "F",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 0.5, -0.2, COL["lead"], 0.09),
            line(1, 0, 0.5, -0.2, COL["lead"], 0.09),
            ellipse(0.5, -0.9, 0.72, 0.55, "#e8c72c", "#a89020"),
            text(0.5, -0.82, "050", size=0.3, color="#5c4410"),
        ],
        "label": {"text": "PTC", "x": 0.5, "y": 0.44, "size": 0.26, "color": "#9fb0c0"},
    })


# ===========================================================================
# Discrete semiconductors
# ===========================================================================

LED_COLORS = [
    ("Red", "#e02b25"), ("Green", "#2fbf4e"), ("Blue", "#2b7fe0"),
    ("Yellow", "#e8c72c"), ("White", "#eef2f6"), ("Orange", "#e88227"),
    ("Pink", "#ef7fb0"), ("Purple", "#9d5cd8"), ("Amber", "#ffb000"),
]


def build_discrete():
    for name, hexc in LED_COLORS:
        add(led(name, hexc, 5, 2))
        add(led(name, hexc, 3, 2))

    add({
        "id": "led-rgb-5mm-cc", "name": "RGB LED 5 mm", "subtitle": "common cathode",
        "category": "discrete", "tags": ["led", "rgb", "common cathode", "5mm"],
        "designator": "D",
        "footprint": {"cols": 4, "rows": 1},
        "pins": [pin(0, 0, "R", 1, "power"), pin(1, 0, "K", 2, "gnd"),
                 pin(2, 0, "G", 3, "power"), pin(3, 0, "B", 4, "power")],
        "shapes": [
            line(0, 0, 1.5, -0.1, COL["lead"], 0.09),
            line(1, 0, 1.5, -0.1, COL["lead"], 0.09),
            line(2, 0, 1.5, -0.1, COL["lead"], 0.09),
            line(3, 0, 1.5, -0.1, COL["lead"], 0.09),
            circle(1.5, -0.55, 0.55, "#dfe5ec", "#a8aeb6", sw=0.05),
            circle(1.28, -0.72, 0.19, "#e02b25"),
            circle(1.72, -0.72, 0.19, "#2fbf4e"),
            circle(1.5, -0.36, 0.19, "#2b7fe0"),
        ],
        "label": {"text": "RGB", "x": 1.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    })

    add(axial_diode("1n4148", "1N4148", "small-signal switching, 100 V",
                    "#111417", "#3a4048", tags=["signal", "switching", "fast"]))
    add(axial_diode("1n4007", "1N4007", "rectifier, 1 A / 1000 V",
                    "#d8d8d8", "#2a2f36", tags=["rectifier", "power"]))
    add(axial_diode("1n5819", "1N5819", "Schottky, 1 A / 40 V",
                    "#d8d8d8", "#2a2f36", tags=["schottky", "low drop"]))
    add(axial_diode("1n5408", "1N5408", "rectifier, 3 A / 1000 V",
                    "#d8d8d8", "#3a2a22", span=4, tags=["rectifier", "power"]))
    add(axial_diode("1n4001", "1N4001", "rectifier, 1 A / 50 V",
                    "#d8d8d8", "#2a2f36", tags=["rectifier", "power"]))
    add(axial_diode("1n4004", "1N4004", "rectifier, 1 A / 400 V",
                    "#d8d8d8", "#2a2f36", tags=["rectifier", "power"]))
    add(axial_diode("1n5822", "1N5822", "Schottky, 3 A / 40 V",
                    "#d8d8d8", "#3a2a22", span=4,
                    tags=["schottky", "low drop", "power"]))
    add(axial_diode("bat85", "BAT85", "Schottky signal, 30 V",
                    "#111417", "#3a4048", tags=["schottky", "signal", "detector"]))
    for v in ("3V3", "5V1", "6V2", "9V1", "12V", "15V", "18V", "24V"):
        add(axial_diode(f"zener-{v.lower()}", f"Zener {v}", "500 mW BZX55",
                        "#111417", "#2f4a6b", tags=["zener", "reference", "clamp"]))

    for mid, name, sub, order, tags in (
        ("bc547", "BC547", "NPN, 45 V / 100 mA", ["C", "B", "E"], ["npn", "small signal"]),
        ("bc557", "BC557", "PNP, 45 V / 100 mA", ["C", "B", "E"], ["pnp", "small signal"]),
        ("bc337", "BC337", "NPN, 45 V / 800 mA", ["C", "B", "E"], ["npn", "medium power"]),
        ("2n2222a", "2N2222A", "NPN, 40 V / 800 mA", ["E", "B", "C"], ["npn", "classic"]),
        ("2n3904", "2N3904", "NPN, 40 V / 200 mA", ["E", "B", "C"], ["npn", "small signal"]),
        ("2n3906", "2N3906", "PNP, 40 V / 200 mA", ["E", "B", "C"], ["pnp", "small signal"]),
        ("s8050", "S8050", "NPN, 25 V / 700 mA", ["E", "B", "C"], ["npn"]),
        ("s8550", "S8550", "PNP, 25 V / 700 mA", ["E", "B", "C"], ["pnp"]),
        ("2n7000", "2N7000", "N-MOSFET, 60 V / 200 mA", ["S", "G", "D"],
         ["mosfet", "n-channel", "logic level"]),
        ("bs170", "BS170", "N-MOSFET, 60 V / 500 mA", ["S", "G", "D"],
         ["mosfet", "n-channel"]),
        ("bc548", "BC548", "NPN, 30 V / 100 mA", ["C", "B", "E"], ["npn", "small signal"]),
        ("bc558", "BC558", "PNP, 30 V / 100 mA", ["C", "B", "E"], ["pnp", "small signal"]),
        ("bc327", "BC327", "PNP, 45 V / 800 mA", ["C", "B", "E"], ["pnp", "medium power"]),
        ("2n5551", "2N5551", "NPN, 160 V / 600 mA", ["E", "B", "C"],
         ["npn", "high voltage"]),
        ("2n5401", "2N5401", "PNP, 150 V / 600 mA", ["E", "B", "C"],
         ["pnp", "high voltage"]),
        ("2n2907", "2N2907", "PNP, 60 V / 600 mA", ["E", "B", "C"], ["pnp", "classic"]),
        ("bt169d", "BT169D", "Thyristor / SCR, 400 V / 0.8 A", ["K", "A", "G"],
         ["scr", "thyristor", "ac"]),
    ):
        add(to92(mid, name, sub, order, mark=name, tags=tags))

    for mid, name, sub, order, tags in (
        ("tip120", "TIP120", "NPN Darlington, 60 V / 5 A", ["B", "C", "E"],
         ["darlington", "npn", "power"]),
        ("tip31c", "TIP31C", "NPN, 100 V / 3 A", ["B", "C", "E"], ["npn", "power"]),
        ("irf540n", "IRF540N", "N-MOSFET, 100 V / 33 A", ["G", "D", "S"],
         ["mosfet", "n-channel", "power"]),
        ("irlz44n", "IRLZ44N", "N-MOSFET logic level, 55 V / 47 A", ["G", "D", "S"],
         ["mosfet", "n-channel", "logic level", "power"]),
        ("irf3205", "IRF3205", "N-MOSFET, 55 V / 110 A", ["G", "D", "S"],
         ["mosfet", "n-channel", "power"]),
        ("bt136", "BT136", "Triac, 600 V / 4 A", ["T1", "T2", "G"],
         ["triac", "ac", "phase control"]),
        ("tip122", "TIP122", "NPN Darlington, 100 V / 5 A", ["B", "C", "E"],
         ["darlington", "npn", "power"]),
        ("tip127", "TIP127", "PNP Darlington, 100 V / 5 A", ["B", "C", "E"],
         ["darlington", "pnp", "power"]),
        ("tip41c", "TIP41C", "NPN, 100 V / 6 A", ["B", "C", "E"], ["npn", "power"]),
        ("tip42c", "TIP42C", "PNP, 100 V / 6 A", ["B", "C", "E"], ["pnp", "power"]),
        ("irfz44n", "IRFZ44N", "N-MOSFET, 55 V / 49 A", ["G", "D", "S"],
         ["mosfet", "n-channel", "power"]),
        ("irf9540n", "IRF9540N", "P-MOSFET, -100 V / -23 A", ["G", "D", "S"],
         ["mosfet", "p-channel", "power", "high side"]),
        ("irf510", "IRF510", "N-MOSFET, 100 V / 5.6 A", ["G", "D", "S"],
         ["mosfet", "n-channel", "rf"]),
        ("bta16-600b", "BTA16-600B", "Triac, 600 V / 16 A", ["T1", "T2", "G"],
         ["triac", "ac", "dimmer", "power"]),
    ):
        add(to220(mid, name, sub, order, category="discrete", designator="Q",
                  mark=name, tags=tags))

    add({
        "id": "led-rgb-5mm-ca", "name": "RGB LED 5 mm (CA)", "subtitle": "common anode",
        "category": "discrete", "tags": ["led", "rgb", "common anode", "5mm"],
        "designator": "D",
        "footprint": {"cols": 4, "rows": 1},
        "pins": [pin(0, 0, "R", 1, "gnd"), pin(1, 0, "A", 2, "power"),
                 pin(2, 0, "G", 3, "gnd"), pin(3, 0, "B", 4, "gnd")],
        "shapes": [
            line(0, 0, 1.5, -0.1, COL["lead"], 0.09),
            line(1, 0, 1.5, -0.1, COL["lead"], 0.09),
            line(2, 0, 1.5, -0.1, COL["lead"], 0.09),
            line(3, 0, 1.5, -0.1, COL["lead"], 0.09),
            circle(1.5, -0.55, 0.55, "#dfe5ec", "#a8aeb6", sw=0.05),
            circle(1.28, -0.72, 0.19, "#e02b25"),
            circle(1.72, -0.72, 0.19, "#2fbf4e"),
            circle(1.5, -0.36, 0.19, "#2b7fe0"),
        ],
        "label": {"text": "RGB+", "x": 1.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    })


# ===========================================================================
# Connectors & switches
# ===========================================================================

def build_connector():
    for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 19, 20, 40):
        add(header(n))
    for n in (2, 3, 4, 5, 6, 8, 10, 16, 20, 40):
        add(header(n, female=True))
    for n in (2, 3, 4, 5, 6, 7, 8, 10, 13, 20):
        add(header(n, rows=2))
    for n in (4, 5, 8):
        add(header(n, rows=2, female=True))

    # DIP sockets, so a socketed chip and the chip itself share a footprint.
    for n in (8, 14, 16, 18, 20, 28):
        add(ic_socket(n))
    for n in (24, 40):
        add(ic_socket(n, wide=True))

    # Screw terminals, 5.08 mm pitch (2 holes per way).
    for ways in (2, 3, 4, 5, 6):
        add({
            "id": f"screw-terminal-{ways}p",
            "name": f"Screw terminal {ways}-way",
            "subtitle": "5.08 mm pitch",
            "category": "connector",
            "tags": ["terminal", "screw", "connector", f"{ways}-way"],
            "designator": "J",
            "footprint": {"cols": 2 * ways - 1, "rows": 1},
            "pins": [pin(2 * i, 0, str(i + 1), i + 1, "signal") for i in range(ways)],
            "body": {"x": -0.7, "y": -1.5, "w": 2 * (ways - 1) + 1.4, "h": 2.5,
                     "rx": 0.1, "fill": COL["terminal_green"], "stroke": "#1c5230"},
            "shapes": [circle(2 * i, -0.85, 0.42, "#c9ced6", "#8d949c", sw=0.05)
                       for i in range(ways)]
                      + [line(2 * i - 0.28, -0.85, 2 * i + 0.28, -0.85, "#5c6269", 0.09,
                              "butt") for i in range(ways)],
        })

    for ways in (2, 3, 4, 5, 6, 8):
        add({
            "id": f"jst-xh-{ways}p", "name": f"JST-XH {ways}-pin",
            "subtitle": "2.5 mm keyed header",
            "category": "connector",
            "tags": ["jst", "xh", "connector", f"{ways}-pin"],
            "designator": "J",
            "footprint": {"cols": ways, "rows": 1},
            "pins": [pin(i, 0, str(i + 1), i + 1, "signal") for i in range(ways)],
            "body": {"x": -0.45, "y": -1.2, "w": (ways - 1) + 0.9, "h": 1.9,
                     "rx": 0.08, "fill": COL["plastic_white"], "stroke": "#a9b0b8"},
            "shapes": [rect(-0.3, -1.05, (ways - 1) + 0.6, 0.7, "#d5dae0", "#a9b0b8",
                            rx=0.06)]
                      + [line(i, 0, i, -0.5, COL["tin"], 0.1) for i in range(ways)],
        })

    add({
        "id": "dc-barrel-jack", "name": "DC barrel jack", "subtitle": "5.5 × 2.1 mm, PCB mount",
        "category": "connector", "tags": ["power", "dc", "jack", "barrel"],
        "designator": "J",
        "footprint": {"cols": 4, "rows": 3},
        "pins": [pin(0, 0, "SLEEVE", 1, "gnd"), pin(3, 0, "TIP", 2, "power"),
                 pin(3, 2, "SW", 3, "signal")],
        "body": {"x": -0.6, "y": -0.7, "w": 5.2, "h": 3.4, "rx": 0.12,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [
            circle(1.4, 1.0, 1.0, "#14171a", "#3a4048", sw=0.06),
            circle(1.4, 1.0, 0.34, "#8d949c"),
            rect(-0.5, -0.6, 5.0, 0.5, "#2f343b", None, rx=0.06),
        ],
        "label": {"text": "DC", "x": 3.4, "y": 1.1, "size": 0.34, "color": COL["silk"]},
    })

    add(breakout("usb-c-breakout", "USB-C breakout", "power + data pads",
                 ["VBUS", "GND", "DP", "DM", "CC1", "CC2"], cols=6, rows=5,
                 category="connector", pcb=COL["pcb_black"], mark="USB-C",
                 tags=["usb", "type-c", "power", "breakout"],
                 extra_shapes=[rect(0.6, 3.1, 3.8, 0.9, COL["tin"], "#7f868e", rx=0.42)]))
    add(breakout("micro-usb-breakout", "Micro-USB breakout", "5-pin",
                 ["VBUS", "DM", "DP", "ID", "GND"], cols=5, rows=5,
                 category="connector", pcb=COL["pcb_black"], mark="µUSB",
                 tags=["usb", "micro", "power", "breakout"],
                 extra_shapes=[rect(0.5, 3.2, 3.0, 0.8, COL["tin"], "#7f868e", rx=0.1)]))

    # 6 mm tactile switch: 4 pins, 6.5 mm × 4.5 mm.
    add({
        "id": "tact-switch-6mm", "name": "Tactile switch 6 mm", "subtitle": "4-pin momentary",
        "category": "connector", "tags": ["switch", "button", "tactile", "momentary"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 2},
        "pins": [pin(0, 0, "1A", 1, "signal"), pin(2, 0, "2A", 2, "signal"),
                 pin(0, 1, "1B", 3, "signal"), pin(2, 1, "2B", 4, "signal")],
        "body": {"x": -0.25, "y": -0.6, "w": 2.5, "h": 2.2, "rx": 0.08,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [
            circle(1.0, 0.5, 0.62, "#3a3f47", "#22262c", sw=0.05),
            circle(1.0, 0.5, 0.42, "#c9ced6", "#8d949c", sw=0.04),
        ],
    })
    add({
        "id": "tact-switch-2pin", "name": "Push button 2-pin", "subtitle": "momentary, breadboard",
        "category": "connector", "tags": ["switch", "button", "momentary"],
        "designator": "SW",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "body": {"x": -0.4, "y": -0.9, "w": 1.8, "h": 1.8, "rx": 0.08,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [circle(0.5, 0.0, 0.5, "#c9ced6", "#8d949c", sw=0.05)],
    })
    add({
        "id": "push-button-12mm", "name": "Push button 12 mm", "subtitle": "panel, 4-pin",
        "category": "connector", "tags": ["switch", "button", "panel", "12mm"],
        "designator": "SW",
        "footprint": {"cols": 5, "rows": 3},
        "pins": [pin(0, 0, "1A", 1, "signal"), pin(4, 0, "2A", 2, "signal"),
                 pin(0, 2, "1B", 3, "signal"), pin(4, 2, "2B", 4, "signal")],
        "body": {"x": -0.4, "y": -0.4, "w": 4.8, "h": 2.8, "rx": 0.1,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [circle(2.0, 1.0, 1.45, "#3a3f47", "#22262c", sw=0.06),
                   circle(2.0, 1.0, 1.05, "#d84040", "#8f2020", sw=0.05)],
    })
    add({
        "id": "slide-switch-spdt", "name": "Slide switch SPDT", "subtitle": "3-pin, 2.54 mm",
        "category": "connector", "tags": ["switch", "spdt", "slide", "toggle"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "COM", 2, "signal"),
                 pin(2, 0, "2", 3, "signal")],
        "body": {"x": -0.4, "y": -1.5, "w": 2.8, "h": 1.9, "rx": 0.08,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [
            rect(0.2, -1.3, 1.6, 0.6, "#22262c", "#14171a", rx=0.06),
            rect(0.3, -1.25, 0.6, 0.5, "#c9ced6", "#8d949c", rx=0.06),
            line(0, 0, 0, -0.35, COL["tin"], 0.1),
            line(1, 0, 1, -0.35, COL["tin"], 0.1),
            line(2, 0, 2, -0.35, COL["tin"], 0.1),
        ],
    })
    add({
        "id": "toggle-switch-spdt", "name": "Toggle switch SPDT", "subtitle": "panel mount",
        "category": "connector", "tags": ["switch", "toggle", "spdt", "panel"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "COM", 2, "signal"),
                 pin(2, 0, "2", 3, "signal")],
        "shapes": [
            line(0, 0, 0, -0.6, COL["tin"], 0.11),
            line(1, 0, 1, -0.6, COL["tin"], 0.11),
            line(2, 0, 2, -0.6, COL["tin"], 0.11),
            rect(-0.3, -1.7, 2.6, 1.1, COL["plastic_black"], COL["plastic_edge"], rx=0.08),
            circle(1.0, -2.05, 0.6, "#b9c0c8", "#7f868e", sw=0.06),
            line(1.0, -2.05, 1.5, -3.1, "#c9ced6", 0.24),
        ],
    })
    add({
        "id": "dip-switch-4p", "name": "DIP switch 4-way", "subtitle": "8-pin, 0.3\"",
        "category": "connector", "tags": ["switch", "dip", "config", "4-way"],
        "designator": "SW",
        "footprint": {"cols": 4, "rows": 4},
        "pins": [pin(0, i, str(i + 1), i + 1, "signal") for i in range(4)]
                + [pin(3, i, str(8 - i), 8 - i, "signal") for i in range(4)],
        "body": {"x": 0.25, "y": -0.4, "w": 2.5, "h": 3.8, "rx": 0.08,
                 "fill": "#c9ced6", "stroke": "#8d949c"},
        "shapes": [rect(0.9, i - 0.28, 1.2, 0.56, "#e8402c", "#a8281c", rx=0.05)
                   for i in range(4)]
                  + [rect(0.95, i - 0.24, 0.5, 0.48, "#f4f6f8", None, rx=0.04)
                     for i in range(4)]
                  + [line(0, i, 0.25, i, COL["tin"], 0.1) for i in range(4)]
                  + [line(3, i, 2.75, i, COL["tin"], 0.1) for i in range(4)],
    })
    add({
        "id": "rotary-encoder-ec11", "name": "Rotary encoder EC11", "subtitle": "with push switch",
        "category": "connector", "tags": ["encoder", "rotary", "ec11", "knob"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 6},
        "pins": [pin(0, 0, "A", 1, "signal"), pin(1, 0, "C", 2, "gnd"),
                 pin(2, 0, "B", 3, "signal"),
                 pin(0, 5, "SW1", 4, "signal"), pin(2, 5, "SW2", 5, "signal")],
        "body": {"x": -0.7, "y": 0.4, "w": 3.4, "h": 4.2, "rx": 0.1,
                 "fill": "#c9ced6", "stroke": "#8d949c"},
        "shapes": [
            circle(1.0, 2.5, 1.35, "#b9c0c8", "#7f868e", sw=0.06),
            circle(1.0, 2.5, 0.75, "#3a3f47", "#22262c", sw=0.05),
            line(0, 0, 0, 0.4, COL["tin"], 0.1),
            line(1, 0, 1, 0.4, COL["tin"], 0.1),
            line(2, 0, 2, 0.4, COL["tin"], 0.1),
            line(0, 5, 0, 4.6, COL["tin"], 0.1),
            line(2, 5, 2, 4.6, COL["tin"], 0.1),
        ],
    })
    add({
        "id": "relay-srd-05vdc", "name": "Relay SRD-05VDC", "subtitle": "5 V SPDT, 10 A",
        "category": "connector", "tags": ["relay", "spdt", "5v", "songle", "switch"],
        "designator": "K",
        "footprint": {"cols": 5, "rows": 4},
        "pins": [pin(0, 0, "COIL+", 1, "power"), pin(0, 3, "COIL-", 2, "gnd"),
                 pin(4, 0, "NC", 3, "signal"), pin(4, 1, "COM", 4, "signal"),
                 pin(4, 3, "NO", 5, "signal")],
        "body": {"x": -0.5, "y": -0.5, "w": 6.0, "h": 4.6, "rx": 0.1,
                 "fill": COL["relay_blue"], "stroke": "#0f3468"},
        "shapes": [rect(-0.35, -0.35, 5.7, 4.3, "#2359a8", None, rx=0.08)],
        "label": {"text": "SRD-05VDC", "x": 2.5, "y": 1.7, "size": 0.42,
                  "color": COL["silk"]},
    })
    add(breakout("relay-module-1ch", "Relay module 1-ch", "opto-isolated, 5 V",
                 ["DC+", "DC-", "IN"], cols=17, rows=11, category="connector",
                 pcb=COL["pcb_blue"], mark="RELAY 1CH", label_size=0.55,
                 tags=["relay", "module", "opto", "5v"],
                 extra_shapes=[rect(6.0, 2.5, 8.0, 6.5, COL["relay_blue"], "#0f3468", rx=0.1),
                               rect(0.5, 6.0, 4.5, 4.0, COL["terminal_green"], "#1c5230",
                                    rx=0.1)]))
    for ch, cols_, rows_ in ((2, 22, 11), (4, 30, 20)):
        add(breakout(f"relay-module-{ch}ch", f"Relay module {ch}-ch",
                     "opto-isolated, 5 V",
                     ["VCC", "GND"] + [f"IN{i + 1}" for i in range(ch)],
                     cols=cols_, rows=rows_, category="connector",
                     pcb=COL["pcb_blue"], mark=f"RELAY {ch}CH", label_size=0.6,
                     tags=["relay", "module", "opto", "5v", f"{ch}-channel"],
                     extra_shapes=[rect(3.0 + i * 5.0, rows_ * 0.35, 4.2, 5.6,
                                        COL["relay_blue"], "#0f3468", rx=0.1)
                                   for i in range(ch)]))
    add({
        "id": "relay-srd-12vdc", "name": "Relay SRD-12VDC", "subtitle": "12 V SPDT, 10 A",
        "category": "connector", "tags": ["relay", "spdt", "12v", "songle", "switch"],
        "designator": "K",
        "footprint": {"cols": 5, "rows": 4},
        "pins": [pin(0, 0, "COIL+", 1, "power"), pin(0, 3, "COIL-", 2, "gnd"),
                 pin(4, 0, "NC", 3, "signal"), pin(4, 1, "COM", 4, "signal"),
                 pin(4, 3, "NO", 5, "signal")],
        "body": {"x": -0.5, "y": -0.5, "w": 6.0, "h": 4.6, "rx": 0.1,
                 "fill": COL["relay_blue"], "stroke": "#0f3468"},
        "shapes": [rect(-0.35, -0.35, 5.7, 4.3, "#2359a8", None, rx=0.08)],
        "label": {"text": "SRD-12VDC", "x": 2.5, "y": 1.7, "size": 0.42,
                  "color": COL["silk"]},
    })

    # -- more switches --------------------------------------------------------
    for ways in (2, 8):
        add({
            "id": f"dip-switch-{ways}p", "name": f"DIP switch {ways}-way",
            "subtitle": f"{2 * ways}-pin, 0.3 in",
            "category": "connector",
            "tags": ["switch", "dip", "config", f"{ways}-way"],
            "designator": "SW",
            "footprint": {"cols": 4, "rows": ways},
            "pins": [pin(0, i, str(i + 1), i + 1, "signal") for i in range(ways)]
                    + [pin(3, i, str(2 * ways - i), 2 * ways - i, "signal")
                       for i in range(ways)],
            "body": {"x": 0.25, "y": -0.4, "w": 2.5, "h": (ways - 1) + 0.8, "rx": 0.08,
                     "fill": "#c9ced6", "stroke": "#8d949c"},
            "shapes": [rect(0.9, i - 0.28, 1.2, 0.56, "#e8402c", "#a8281c", rx=0.05)
                       for i in range(ways)]
                      + [rect(0.95, i - 0.24, 0.5, 0.48, "#f4f6f8", None, rx=0.04)
                         for i in range(ways)]
                      + [line(0, i, 0.25, i, COL["tin"], 0.1) for i in range(ways)]
                      + [line(3, i, 2.75, i, COL["tin"], 0.1) for i in range(ways)],
        })
    add({
        "id": "toggle-switch-dpdt", "name": "Toggle switch DPDT", "subtitle": "panel mount, 6-pin",
        "category": "connector", "tags": ["switch", "toggle", "dpdt", "panel"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 2},
        "pins": [pin(0, 0, "1A", 1, "signal"), pin(1, 0, "COM A", 2, "signal"),
                 pin(2, 0, "2A", 3, "signal"),
                 pin(0, 1, "1B", 4, "signal"), pin(1, 1, "COM B", 5, "signal"),
                 pin(2, 1, "2B", 6, "signal")],
        "shapes": [
            rect(-0.4, -1.5, 2.8, 1.2, COL["plastic_black"], COL["plastic_edge"], rx=0.08),
            circle(1.0, -1.9, 0.6, "#b9c0c8", "#7f868e", sw=0.06),
            line(1.0, -1.9, 1.5, -2.95, "#c9ced6", 0.24),
        ]
        + [line(c, r, c, -0.3, COL["tin"], 0.1) for r in (0, 1) for c in (0, 1, 2)],
    })
    add({
        "id": "slide-switch-dpdt", "name": "Slide switch DPDT", "subtitle": "6-pin, 2.54 mm",
        "category": "connector", "tags": ["switch", "dpdt", "slide"],
        "designator": "SW",
        "footprint": {"cols": 3, "rows": 2},
        "pins": [pin(0, 0, "1A", 1, "signal"), pin(1, 0, "COM A", 2, "signal"),
                 pin(2, 0, "2A", 3, "signal"),
                 pin(0, 1, "1B", 4, "signal"), pin(1, 1, "COM B", 5, "signal"),
                 pin(2, 1, "2B", 6, "signal")],
        "body": {"x": -0.4, "y": -1.5, "w": 2.8, "h": 2.9, "rx": 0.08,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [rect(0.2, -1.3, 1.6, 0.6, "#22262c", "#14171a", rx=0.06),
                   rect(0.3, -1.25, 0.6, 0.5, "#c9ced6", "#8d949c", rx=0.06)],
    })

    # -- panel and board-to-board connectors ---------------------------------
    add({
        "id": "audio-jack-3-5mm", "name": "Audio jack 3.5 mm", "subtitle": "stereo, PCB mount",
        "category": "connector", "tags": ["audio", "jack", "3.5mm", "stereo", "trs"],
        "designator": "J",
        "footprint": {"cols": 5, "rows": 3},
        "pins": [pin(0, 0, "T", 1, "signal"), pin(0, 2, "R", 2, "signal"),
                 pin(4, 1, "S", 3, "gnd")],
        "body": {"x": -0.6, "y": -0.6, "w": 6.2, "h": 3.4, "rx": 0.12,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [circle(0.6, 1.0, 0.85, "#14171a", "#3a4048", sw=0.06),
                   circle(0.6, 1.0, 0.34, "#5c6269"),
                   rect(1.8, 0.1, 3.4, 1.8, "#2f343b", None, rx=0.08)],
        "label": {"text": "3.5", "x": 3.4, "y": 1.1, "size": 0.36, "color": COL["silk"]},
    })
    add({
        "id": "banana-jack", "name": "Banana jack 4 mm", "subtitle": "panel binding post",
        "category": "connector", "tags": ["banana", "jack", "4mm", "test", "panel"],
        "designator": "J",
        "footprint": {"cols": 1, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal")],
        "shapes": [circle(0, 0, 1.5, "#d84040", "#8f2020", sw=0.08),
                   circle(0, 0, 0.85, "#c9ced6", "#8d949c", sw=0.06),
                   circle(0, 0, 0.42, "#14171a")],
    })
    add(breakout("rj45-jack", "RJ45 jack", "8P8C Ethernet, PCB mount",
                 ["1", "2", "3", "4", "5", "6", "7", "8"], cols=8, rows=7,
                 category="connector", pcb=COL["plastic_black"], pcb_edge="#0e1116",
                 mark="RJ45", tags=["ethernet", "rj45", "8p8c", "lan", "network"],
                 extra_shapes=[rect(0.6, 2.0, 5.8, 4.0, "#3a4048", "#22262c", rx=0.1),
                               rect(2.0, 2.4, 3.0, 1.4, "#0b0e12", None, rx=0.06)]))
    add(breakout("db9-male", "D-SUB 9 male", "RS-232 / serial",
                 ["1", "2", "3", "4", "5", "6", "7", "8", "9"], cols=12, rows=5,
                 category="connector", pcb=COL["steel"], pcb_edge="#6f767e",
                 mark="DB9", tags=["db9", "d-sub", "serial", "rs232"],
                 extra_shapes=[rect(1.4, 1.6, 9.0, 2.4, "#3a4048", "#22262c", rx=0.9)]))
    add(breakout("usb-a-female", "USB-A female", "host / power socket",
                 ["VBUS", "DM", "DP", "GND"], cols=6, rows=6, category="connector",
                 pcb=COL["steel"], pcb_edge="#6f767e", mark="USB-A",
                 tags=["usb", "usb-a", "host", "socket", "power"],
                 extra_shapes=[rect(0.6, 1.8, 3.8, 3.2, "#c9ced6", "#8d949c", rx=0.08),
                               rect(1.1, 2.4, 2.8, 1.2, "#e9edf1", None, rx=0.04)]))
    add(breakout("sd-card-module", "microSD card module", "SPI card socket",
                 ["GND", "VCC", "MISO", "MOSI", "SCK", "CS"], cols=10, rows=9,
                 category="connector", pcb=COL["pcb_blue"], mark="microSD",
                 label_size=0.5, tags=["sd", "microsd", "storage", "spi", "card"],
                 extra_shapes=[rect(1.0, 2.4, 7.4, 5.0, COL["steel"], "#6f767e", rx=0.1)]))
    add({
        "id": "jst-ph-2p", "name": "JST-PH 2-pin", "subtitle": "2.0 mm LiPo connector",
        "category": "connector", "tags": ["jst", "ph", "lipo", "battery", "2mm"],
        "designator": "J",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(1, 0, "-", 2, "gnd")],
        "body": {"x": -0.4, "y": -1.1, "w": 1.8, "h": 1.7, "rx": 0.08,
                 "fill": COL["plastic_white"], "stroke": "#a9b0b8"},
        "shapes": [rect(-0.26, -0.95, 1.52, 0.62, "#d5dae0", "#a9b0b8", rx=0.06),
                   line(0, 0, 0, -0.45, COL["tin"], 0.1),
                   line(1, 0, 1, -0.45, COL["tin"], 0.1)],
    })


# ===========================================================================
# Wireless & comms
# ===========================================================================

def build_comms():
    add(breakout("hc-05", "HC-05 Bluetooth", "SPP serial, master/slave",
                 ["VCC", "GND", "TXD", "RXD", "STATE", "EN"],
                 cols=6, rows=11, category="comms", pcb=COL["pcb_blue"], mark="HC-05",
                 tags=["bluetooth", "serial", "uart", "wireless"]))
    add(breakout("hc-06", "HC-06 Bluetooth", "SPP serial, slave only",
                 ["VCC", "GND", "TXD", "RXD"], cols=4, rows=11, category="comms",
                 pcb=COL["pcb_blue"], mark="HC-06",
                 tags=["bluetooth", "serial", "uart", "wireless"]))
    add({
        "id": "nrf24l01", "name": "nRF24L01+", "subtitle": "2.4 GHz transceiver",
        "category": "comms", "tags": ["nrf24", "2.4ghz", "spi", "wireless", "radio"],
        "designator": "U",
        "footprint": {"cols": 2, "rows": 4},
        "pins": [pin(0, 0, "GND", 1, "gnd"), pin(1, 0, "VCC", 2, "power"),
                 pin(0, 1, "CE", 3, "signal"), pin(1, 1, "CSN", 4, "signal"),
                 pin(0, 2, "SCK", 5, "signal"), pin(1, 2, "MOSI", 6, "signal"),
                 pin(0, 3, "MISO", 7, "signal"), pin(1, 3, "IRQ", 8, "signal")],
        "body": {"x": -0.5, "y": -0.5, "w": 8.5, "h": 4.0, "rx": 0.14,
                 "fill": COL["pcb_black"], "stroke": COL["ic_edge"]},
        "shapes": [
            rect(-0.32, -0.32, 1.64, 3.64, COL["plastic_black"], COL["ic_edge"], rx=0.08),
            rect(2.2, 0.2, 3.2, 2.6, COL["steel"], "#6f767e", rx=0.08),
            path("M 6.0 2.8 L 7.6 2.8 L 7.6 0.2 L 6.4 0.2 L 6.4 1.2 L 7.2 1.2",
                 stroke=COL["copper"], sw=0.16),
        ],
        "label": {"text": "nRF24L01+", "x": 4.0, "y": 3.2, "size": 0.34,
                  "color": COL["silk"]},
    })
    add(breakout("lora-ra-02", "LoRa RA-02", "SX1278, 433 MHz",
                 ["GND", "3V3", "RST", "DIO0", "DIO1", "DIO2", "DIO3", "DIO4",
                  "DIO5", "MISO", "MOSI", "SCK", "NSS", "GND"],
                 cols=14, rows=10, category="comms", pcb=COL["pcb_black"],
                 mark="RA-02", label_size=0.5,
                 tags=["lora", "sx1278", "433mhz", "spi", "wireless"]))
    add(breakout("rc522-rfid", "RC522 RFID", "13.56 MHz MFRC522",
                 ["SDA", "SCK", "MOSI", "MISO", "IRQ", "GND", "RST", "3V3"],
                 cols=8, rows=15, category="comms", pcb=COL["pcb_red"],
                 pcb_edge="#4a0f18", mark="RC522", label_size=0.5,
                 tags=["rfid", "nfc", "mfrc522", "spi", "13.56mhz"]))
    add({
        "id": "esp-01s", "name": "ESP-01S", "subtitle": "ESP8266 serial Wi-Fi",
        "category": "comms", "tags": ["esp8266", "esp-01", "wifi", "uart"],
        "designator": "U",
        "footprint": {"cols": 2, "rows": 4},
        "pins": [pin(0, 0, "GND", 1, "gnd"), pin(1, 0, "TX", 2, "signal"),
                 pin(0, 1, "GPIO2", 3, "io"), pin(1, 1, "CH_PD", 4, "signal"),
                 pin(0, 2, "GPIO0", 5, "io"), pin(1, 2, "RST", 6, "signal"),
                 pin(0, 3, "RX", 7, "signal"), pin(1, 3, "VCC", 8, "power")],
        "body": {"x": -0.5, "y": -0.5, "w": 5.5, "h": 4.0, "rx": 0.14,
                 "fill": COL["pcb_black"], "stroke": COL["ic_edge"]},
        "shapes": [
            rect(-0.32, -0.32, 1.64, 3.64, COL["plastic_black"], COL["ic_edge"], rx=0.08),
            rect(2.0, 0.3, 1.6, 2.4, COL["steel"], "#6f767e", rx=0.08),
            path("M 4.2 2.6 L 4.2 0.4 L 4.9 0.4", stroke=COL["copper"], sw=0.16),
        ],
        "label": {"text": "ESP-01S", "x": 2.2, "y": 3.2, "size": 0.32, "color": COL["silk"]},
    })
    add(breakout("sim800l", "SIM800L", "quad-band GSM / GPRS",
                 ["NET", "VCC", "RST", "RXD", "TXD", "GND", "RING", "DTR"],
                 cols=10, rows=12, category="comms", pcb=COL["pcb_blue"],
                 mark="SIM800L", label_size=0.5,
                 tags=["gsm", "gprs", "sim800", "cellular", "sms"]))
    add(breakout("neo-6m-gps", "NEO-6M GPS", "u-blox receiver",
                 ["VCC", "RX", "TX", "GND"], cols=12, rows=10, category="comms",
                 pcb=COL["pcb_blue"], mark="NEO-6M", label_size=0.5,
                 tags=["gps", "gnss", "ublox", "uart"]))
    add(breakout("w5500-ethernet", "W5500 Ethernet", "hardware TCP/IP, SPI",
                 ["VCC", "GND", "MOSI", "MISO", "SCK", "CS", "RST", "INT"],
                 cols=14, rows=16, category="comms", pcb=COL["pcb_blue"],
                 mark="W5500", label_size=0.55,
                 tags=["ethernet", "w5500", "spi", "network", "lan"]))
    add(breakout("enc28j60", "ENC28J60", "10 Mbit Ethernet, SPI",
                 ["VCC", "GND", "MOSI", "MISO", "SCK", "CS", "RST", "INT"],
                 cols=14, rows=16, category="comms", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="ENC28J60", label_size=0.55,
                 tags=["ethernet", "enc28j60", "spi", "network"]))
    add(breakout("max485-module", "MAX485 module", "RS-485 transceiver",
                 ["VCC", "A", "B", "GND", "RO", "RE", "DE", "DI"],
                 cols=8, rows=6, category="comms", pcb=COL["pcb_blue"],
                 mark="MAX485", tags=["rs485", "modbus", "serial", "differential"]))
    add(breakout("mcp2515-module", "MCP2515 CAN", "CAN bus + TJA1050",
                 ["VCC", "GND", "CS", "SO", "SI", "SCK", "INT"],
                 cols=12, rows=12, category="comms", pcb=COL["pcb_blue"],
                 mark="MCP2515", label_size=0.5,
                 tags=["can", "mcp2515", "spi", "bus", "automotive"]))
    add(breakout("ftdi-ft232rl", "FT232RL USB-UART", "FTDI serial adapter",
                 ["DTR", "RX", "TX", "VCC", "CTS", "GND"], cols=6, rows=10,
                 category="comms", pcb=COL["pcb_red"], pcb_edge="#4a0f18",
                 mark="FT232RL", tags=["usb", "uart", "ftdi", "serial", "programmer"]))
    add(breakout("ch340-usb-ttl", "CH340 USB-TTL", "serial adapter",
                 ["VCC", "TXD", "RXD", "GND"], cols=5, rows=10, category="comms",
                 pcb=COL["pcb_blue"], mark="CH340",
                 tags=["usb", "uart", "ch340", "serial", "programmer"]))
    add(to92("tsop38238", "TSOP38238", "38 kHz IR receiver", ["OUT", "GND", "VS"],
             category="comms", designator="U", mark="IR RX",
             tags=["infrared", "receiver", "remote", "38khz"]))
    add({
        "id": "ir-led-940", "name": "IR LED 940 nm", "subtitle": "5 mm emitter",
        "category": "comms", "tags": ["infrared", "led", "emitter", "940nm"],
        "designator": "D",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "A", 1, "power"), pin(1, 0, "K", 2, "gnd")],
        "shapes": [
            line(0, 0, 0.5, 0, COL["lead"], 0.1),
            line(1, 0, 0.5, 0, COL["lead"], 0.1),
            circle(0.5, 0, 0.52, "#2b3a6b", "#16204a", sw=0.05),
            circle(0.5, 0, 0.3, "#4257a0", None),
            line(0.95, -0.26, 0.95, 0.26, "#16204a", 0.09, "butt"),
        ],
        "label": {"text": "IR", "x": 0.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    })
    add(breakout("rf-433-tx", "433 MHz TX", "ASK transmitter",
                 ["DATA", "VCC", "GND"], cols=6, rows=6, category="comms",
                 pcb=COL["pcb_green"], pcb_edge=COL["pcb_green_edge"], mark="433 TX",
                 tags=["433mhz", "rf", "transmitter", "ask"]))
    add(breakout("rf-433-rx", "433 MHz RX", "ASK receiver",
                 ["VCC", "DATA", "DATA", "GND"], cols=12, rows=8, category="comms",
                 pcb=COL["pcb_green"], pcb_edge=COL["pcb_green_edge"], mark="433 RX",
                 label_size=0.5, tags=["433mhz", "rf", "receiver", "ask"]))

    # nRF24L01+ PA/LNA: same 2x4 header as the bare module, but the board runs
    # on past it to the power amplifier can and the SMA antenna socket.
    add({
        "id": "nrf24l01-pa-lna", "name": "nRF24L01+ PA/LNA",
        "subtitle": "2.4 GHz, +20 dBm, SMA antenna",
        "category": "comms",
        "tags": ["nrf24", "nrf24l01", "pa", "lna", "2.4ghz", "spi", "wireless",
                 "radio", "long range", "sma"],
        "designator": "U",
        "footprint": {"cols": 2, "rows": 4},
        "pins": [pin(0, 0, "GND", 1, "gnd"), pin(1, 0, "VCC", 2, "power"),
                 pin(0, 1, "CE", 3, "signal"), pin(1, 1, "CSN", 4, "signal"),
                 pin(0, 2, "SCK", 5, "signal"), pin(1, 2, "MOSI", 6, "signal"),
                 pin(0, 3, "MISO", 7, "signal"), pin(1, 3, "IRQ", 8, "signal")],
        "body": {"x": -0.5, "y": -1.1, "w": 16.5, "h": 5.7, "rx": 0.16,
                 "fill": COL["pcb_black"], "stroke": COL["ic_edge"]},
        "shapes": [
            rect(-0.32, -0.32, 1.64, 3.64, COL["plastic_black"], COL["ic_edge"], rx=0.08),
            # RF shield can over the nRF24 + PA/LNA front end
            rect(2.2, -0.8, 9.0, 5.1, COL["steel"], "#6f767e", rx=0.1),
            rect(2.6, -0.45, 3.6, 4.4, "#8d949c", "#6f767e", rx=0.06),
            # SMA / RP-SMA socket on the far end
            rect(12.0, 0.4, 2.3, 2.4, COL["tin"], "#7f868e", rx=0.18),
            circle(13.15, 1.6, 0.85, COL["gold"], "#8a6f1a", sw=0.06),
            circle(13.15, 1.6, 0.24, "#e8e2c8"),
            rect(14.3, 1.15, 1.6, 0.9, COL["steel"], "#7f868e", rx=0.1),
        ],
        "label": {"text": "nRF24L01+ PA/LNA", "x": 6.7, "y": 4.05, "size": 0.42,
                  "color": COL["silk"]},
    })
    add(breakout("nrf24l01-adapter", "nRF24L01 adapter", "socket board with 3.3 V LDO",
                 ["VCC", "GND", "CE", "CSN", "SCK", "MOSI", "MISO", "IRQ"],
                 cols=8, rows=8, category="comms", pcb=COL["pcb_blue"],
                 mark="nRF24 ADAPTER", label_size=0.42,
                 tags=["nrf24", "adapter", "socket", "regulator", "5v tolerant"],
                 extra_shapes=[rect(1.6, 2.6, 4.0, 3.6, COL["plastic_black"],
                                    COL["gold"], rx=0.08)]))

    # -- more radios ---------------------------------------------------------
    add(breakout("lora-e32-433", "Ebyte E32-433T", "SX1278 UART LoRa, 1 W",
                 ["M0", "M1", "RXD", "TXD", "AUX", "VCC", "GND"],
                 cols=8, rows=17, category="comms", pcb=COL["pcb_black"],
                 mark="E32-433T", label_size=0.42,
                 tags=["lora", "sx1278", "433mhz", "uart", "long range", "ebyte"]))
    add(breakout("rfm95-lora", "RFM95W LoRa", "SX1276, 868/915 MHz SPI",
                 ["GND", "MISO", "MOSI", "SCK", "NSS", "RST", "DIO0", "DIO1",
                  "DIO2", "3V3"],
                 cols=10, rows=8, category="comms", pcb=COL["pcb_black"],
                 mark="RFM95W", label_size=0.45,
                 tags=["lora", "sx1276", "868mhz", "915mhz", "spi", "hoperf"]))
    add(breakout("rfm69hcw", "RFM69HCW", "868/915 MHz FSK, +20 dBm",
                 ["GND", "MISO", "MOSI", "SCK", "NSS", "RST", "DIO0", "DIO1",
                  "DIO2", "3V3"],
                 cols=10, rows=8, category="comms", pcb=COL["pcb_black"],
                 mark="RFM69HCW", label_size=0.42,
                 tags=["fsk", "868mhz", "915mhz", "spi", "packet radio", "hoperf"]))
    add(breakout("hc-12", "HC-12", "433 MHz transparent UART, 1 km",
                 ["VCC", "GND", "RXD", "TXD", "SET"], cols=10, rows=11,
                 category="comms", pcb=COL["pcb_blue"], mark="HC-12",
                 label_size=0.5, tags=["433mhz", "uart", "transparent", "si4463",
                                       "long range"]))
    add(breakout("hm-10-ble", "HM-10 BLE", "CC2541 Bluetooth 4.0",
                 ["VCC", "GND", "TXD", "RXD"], cols=8, rows=10, category="comms",
                 pcb=COL["pcb_blue"], mark="HM-10",
                 tags=["ble", "bluetooth", "cc2541", "uart", "wireless"]))

    # -- more wired links ----------------------------------------------------
    add(breakout("cp2102-usb-uart", "CP2102 USB-UART", "Silabs serial adapter",
                 ["3V3", "TXD", "RXD", "GND", "5V", "DTR"], cols=6, rows=10,
                 category="comms", pcb=COL["pcb_blue"], mark="CP2102",
                 tags=["usb", "uart", "cp2102", "serial", "programmer"]))
    add(breakout("max3232-module", "MAX3232 module", "RS-232 level shifter",
                 ["VCC", "GND", "TXD", "RXD"], cols=10, rows=8, category="comms",
                 pcb=COL["pcb_blue"], mark="MAX3232", label_size=0.5,
                 tags=["rs232", "level shifter", "serial", "max3232"]))
    add(breakout("lan8720", "LAN8720 PHY", "RMII 10/100 Ethernet PHY",
                 ["VCC", "GND", "TX1", "TX0", "TXEN", "RX0", "RX1", "CRS",
                  "MDIO", "MDC", "NINT", "CLK"],
                 cols=14, rows=13, category="comms", pcb=COL["pcb_blue"],
                 mark="LAN8720", label_size=0.5,
                 tags=["ethernet", "phy", "rmii", "lan8720", "network"]))

    # -- IR and RFID ---------------------------------------------------------
    add(to92("vs1838b", "VS1838B", "38 kHz IR receiver", ["OUT", "GND", "VS"],
             category="comms", designator="U", mark="IR RX",
             tags=["infrared", "receiver", "remote", "38khz"]))
    add(breakout("rdm6300-rfid", "RDM6300 RFID", "125 kHz EM4100 reader",
                 ["ANT1", "ANT2", "GND", "5V", "TX", "RX"], cols=17, rows=8,
                 category="comms", pcb=COL["pcb_black"], mark="RDM6300",
                 label_size=0.55, tags=["rfid", "125khz", "em4100", "uart", "reader"]))
    add(breakout("pn532-nfc", "PN532 NFC", "13.56 MHz NFC / RFID, I2C / SPI",
                 ["VCC", "GND", "SDA", "SCL", "IRQ", "RSTO"], cols=17, rows=17,
                 category="comms", pcb=COL["pcb_red"], pcb_edge="#4a0f18",
                 mark="PN532", label_size=0.7,
                 tags=["nfc", "rfid", "pn532", "i2c", "spi", "13.56mhz"]))


# ===========================================================================
# Motors & drivers
# ===========================================================================

def build_motor():
    add(breakout("l298n-module", "L298N module", "dual H-bridge, 2 A",
                 ["ENA", "IN1", "IN2", "IN3", "IN4", "ENB"],
                 cols=17, rows=17, category="motor", pcb=COL["pcb_red"],
                 pcb_edge="#4a0f18", mark="L298N", label_size=0.8,
                 tags=["motor", "h-bridge", "l298", "driver", "dc"],
                 extra_shapes=[rect(4.0, 4.0, 9.0, 6.0, COL["heatsink"], "#6b737b", rx=0.1),
                               rect(0.5, 12.0, 6.0, 4.0, COL["terminal_green"],
                                    "#1c5230", rx=0.1)]))
    add({
        "id": "a4988-driver", "name": "A4988 stepper driver", "subtitle": "Pololu-style carrier",
        "category": "motor", "tags": ["stepper", "a4988", "driver", "motor", "pololu"],
        "designator": "U",
        "footprint": {"cols": 2, "rows": 8},
        "pins": [pin(0, 0, "ENABLE", 1, "in"), pin(1, 0, "VMOT", 16, "power"),
                 pin(0, 1, "MS1", 2, "in"), pin(1, 1, "GND", 15, "gnd"),
                 pin(0, 2, "MS2", 3, "in"), pin(1, 2, "2B", 14, "out"),
                 pin(0, 3, "MS3", 4, "in"), pin(1, 3, "2A", 13, "out"),
                 pin(0, 4, "RESET", 5, "in"), pin(1, 4, "1A", 12, "out"),
                 pin(0, 5, "SLEEP", 6, "in"), pin(1, 5, "1B", 11, "out"),
                 pin(0, 6, "STEP", 7, "in"), pin(1, 6, "VDD", 10, "power"),
                 pin(0, 7, "DIR", 8, "in"), pin(1, 7, "GND", 9, "gnd")],
        "body": {"x": -0.5, "y": -0.5, "w": 6.0, "h": 8.0, "rx": 0.14,
                 "fill": COL["pcb_green"], "stroke": COL["pcb_green_edge"]},
        "shapes": [
            rect(-0.32, -0.32, 1.64, 7.64, COL["plastic_black"], COL["ic_edge"], rx=0.08),
            rect(2.4, 2.6, 2.4, 2.4, COL["ic_body"], COL["ic_edge"], rx=0.08),
            circle(3.6, 0.9, 0.5, "#2f6bb5", "#1c4478", sw=0.05),
        ],
        "label": {"text": "A4988", "x": 3.6, "y": 6.6, "size": 0.4, "color": COL["silk"]},
    })
    add({
        "id": "drv8825-driver", "name": "DRV8825 stepper driver", "subtitle": "up to 1/32 step",
        "category": "motor", "tags": ["stepper", "drv8825", "driver", "motor"],
        "designator": "U",
        "footprint": {"cols": 2, "rows": 8},
        "pins": [pin(0, 0, "EN", 1, "in"), pin(1, 0, "VMOT", 16, "power"),
                 pin(0, 1, "M0", 2, "in"), pin(1, 1, "GND", 15, "gnd"),
                 pin(0, 2, "M1", 3, "in"), pin(1, 2, "B2", 14, "out"),
                 pin(0, 3, "M2", 4, "in"), pin(1, 3, "B1", 13, "out"),
                 pin(0, 4, "RESET", 5, "in"), pin(1, 4, "A1", 12, "out"),
                 pin(0, 5, "SLEEP", 6, "in"), pin(1, 5, "A2", 11, "out"),
                 pin(0, 6, "STEP", 7, "in"), pin(1, 6, "FAULT", 10, "out"),
                 pin(0, 7, "DIR", 8, "in"), pin(1, 7, "GND", 9, "gnd")],
        "body": {"x": -0.5, "y": -0.5, "w": 6.0, "h": 8.0, "rx": 0.14,
                 "fill": COL["pcb_purple"], "stroke": "#1c1029"},
        "shapes": [
            rect(-0.32, -0.32, 1.64, 7.64, COL["plastic_black"], COL["ic_edge"], rx=0.08),
            rect(2.4, 2.6, 2.4, 2.4, COL["ic_body"], COL["ic_edge"], rx=0.08),
            circle(3.6, 0.9, 0.5, "#2f6bb5", "#1c4478", sw=0.05),
        ],
        "label": {"text": "DRV8825", "x": 3.6, "y": 6.6, "size": 0.36, "color": COL["silk"]},
    })
    add(breakout("uln2003-stepper-board", "ULN2003 stepper board", "28BYJ-48 driver",
                 ["IN1", "IN2", "IN3", "IN4", "VCC", "GND"],
                 cols=13, rows=11, category="motor", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="ULN2003", label_size=0.55,
                 tags=["stepper", "uln2003", "28byj-48", "driver"]))
    add({
        "id": "servo-header", "name": "Servo header", "subtitle": "3-pin RC servo",
        "category": "motor", "tags": ["servo", "rc", "pwm", "connector"],
        "designator": "J",
        "footprint": {"cols": 1, "rows": 3},
        "pins": [pin(0, 0, "SIG", 1, "signal"), pin(0, 1, "VCC", 2, "power"),
                 pin(0, 2, "GND", 3, "gnd")],
        "body": {"x": -0.36, "y": -0.36, "w": 0.72, "h": 2.72, "rx": 0.08,
                 "fill": COL["plastic_black"], "stroke": COL["plastic_edge"]},
        "shapes": [rect(-0.12, i - 0.12, 0.24, 0.24, COL["gold"]) for i in range(3)]
                  + [rect(0.42, -0.3, 0.2, 0.6, "#e8c72c", None, rx=0.04),
                     rect(0.42, 0.7, 0.2, 0.6, "#d84040", None, rx=0.04),
                     rect(0.42, 1.7, 0.2, 0.6, "#3a3f47", None, rx=0.04)],
    })
    add({
        "id": "motor-terminal-2p", "name": "DC motor terminal", "subtitle": "2-way screw terminal",
        "category": "motor", "tags": ["motor", "terminal", "dc", "connector"],
        "designator": "M",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "M+", 1, "power"), pin(2, 0, "M-", 2, "gnd")],
        "body": {"x": -0.7, "y": -1.5, "w": 3.4, "h": 2.5, "rx": 0.1,
                 "fill": COL["terminal_blue"], "stroke": "#123f75"},
        "shapes": [circle(0, -0.85, 0.42, "#c9ced6", "#8d949c", sw=0.05),
                   circle(2, -0.85, 0.42, "#c9ced6", "#8d949c", sw=0.05),
                   text(1.0, 0.55, "M", size=0.4, color=COL["silk"])],
    })
    add(breakout("mosfet-module", "MOSFET switch module", "IRF520 low-side driver",
                 ["SIG", "VCC", "GND"], cols=13, rows=9, category="motor",
                 pcb=COL["pcb_blue"], mark="IRF520", label_size=0.5,
                 tags=["mosfet", "switch", "pwm", "irf520", "driver"]))

    # -- silent stepper drivers, same StepStick footprint as the A4988 --------
    for mid, name, sub, tags in (
        ("tmc2208", "TMC2208", "silent stepper driver, 1.2 A",
         ["stepper", "trinamic", "silent", "stealthchop", "3d printer"]),
        ("tmc2209", "TMC2209", "silent stepper driver, 2 A + UART",
         ["stepper", "trinamic", "silent", "uart", "3d printer"]),
    ):
        add(breakout(mid, name, sub,
                     ["EN", "MS1", "MS2", "MS3", "RST", "SLP", "STEP", "DIR"],
                     cols=8, rows=8, category="motor", pcb=COL["pcb_red"],
                     pcb_edge="#4a0f18", mark=name, label_size=0.45, tags=tags,
                     extra_shapes=[rect(2.2, 2.4, 3.2, 3.2, COL["ic_body"],
                                        COL["ic_edge"], rx=0.1)]))
    add(breakout("a3967-easydriver", "EasyDriver A3967", "stepper driver, 750 mA",
                 ["GND", "STEP", "DIR", "MS1", "MS2", "EN", "SLP", "RST"],
                 cols=17, rows=13, category="motor", pcb=COL["pcb_red"],
                 pcb_edge="#4a0f18", mark="EASYDRIVER", label_size=0.55,
                 tags=["stepper", "a3967", "driver", "sparkfun"]))
    add(breakout("drv8833-module", "DRV8833 module", "dual H-bridge, 1.5 A / ch",
                 ["VCC", "GND", "AIN1", "AIN2", "BIN1", "BIN2", "SLP", "FLT"],
                 cols=12, rows=10, category="motor", pcb=COL["pcb_red"],
                 pcb_edge="#4a0f18", mark="DRV8833", label_size=0.5,
                 tags=["h-bridge", "dc motor", "drv8833", "driver", "dual"]))
    add(breakout("l9110s-module", "L9110S module", "dual H-bridge, 800 mA",
                 ["B-IA", "B-IB", "GND", "VCC", "A-IA", "A-IB"], cols=10, rows=10,
                 category="motor", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="L9110S", label_size=0.5,
                 tags=["h-bridge", "dc motor", "l9110", "driver", "cheap"]))
    add(breakout("bts7960-module", "BTS7960 module", "half-bridge, 43 A",
                 ["RPWM", "LPWM", "R_EN", "L_EN", "R_IS", "L_IS", "VCC", "GND"],
                 cols=20, rows=16, category="motor", pcb=COL["pcb_red"],
                 pcb_edge="#4a0f18", mark="BTS7960", label_size=0.7,
                 tags=["h-bridge", "high current", "bts7960", "driver", "43a"]))
    add(breakout("pca9685-module", "PCA9685 servo driver", "16-channel PWM, I2C",
                 ["GND", "OE", "SCL", "SDA", "VCC", "V+"], cols=24, rows=10,
                 category="motor", pcb=COL["pcb_green"],
                 pcb_edge=COL["pcb_green_edge"], mark="PCA9685", label_size=0.6,
                 tags=["servo", "pwm", "i2c", "16-channel", "pca9685"],
                 extra_shapes=[rect(2.0 + i * 4.0, 5.0, 3.0, 4.0,
                                    COL["plastic_black"], COL["ic_edge"], rx=0.06)
                               for i in range(5)]))

    add({
        "id": "servo-sg90", "name": "Servo SG90", "subtitle": "9 g micro servo, 3-wire",
        "category": "motor", "tags": ["servo", "sg90", "rc", "pwm", "micro"],
        "designator": "M",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "GND", 1, "gnd"), pin(1, 0, "VCC", 2, "power"),
                 pin(2, 0, "SIG", 3, "signal")],
        "body": {"x": -0.5, "y": -9.0, "w": 4.6, "h": 8.4, "rx": 0.14,
                 "fill": "#2f6bb5", "stroke": "#1c4478"},
        "shapes": [
            rect(-2.2, -7.4, 8.4, 1.4, "#2f6bb5", "#1c4478", rx=0.1),
            circle(1.2, -8.2, 1.4, "#3a3f47", "#22262c", sw=0.06),
            circle(1.2, -8.2, 0.5, "#c9ced6", None),
            line(0, 0, 0, -0.6, COL["lead"], 0.12),
            line(1, 0, 1, -0.6, COL["lead"], 0.12),
            line(2, 0, 2, -0.6, COL["lead"], 0.12),
        ],
        "label": {"text": "SG90", "x": 1.8, "y": -3.4, "size": 0.5, "color": COL["silk"]},
    })
    add({
        "id": "stepper-28byj48-conn", "name": "28BYJ-48 connector",
        "subtitle": "5-wire unipolar stepper header",
        "category": "motor", "tags": ["stepper", "28byj-48", "unipolar", "connector"],
        "designator": "J",
        "footprint": {"cols": 5, "rows": 1},
        "pins": [pin(0, 0, "COM", 1, "power"), pin(1, 0, "A", 2, "out"),
                 pin(2, 0, "B", 3, "out"), pin(3, 0, "C", 4, "out"),
                 pin(4, 0, "D", 5, "out")],
        "body": {"x": -0.45, "y": -1.2, "w": 4.9, "h": 1.9, "rx": 0.08,
                 "fill": COL["plastic_white"], "stroke": "#a9b0b8"},
        "shapes": [rect(-0.3, -1.05, 4.6, 0.7, "#d5dae0", "#a9b0b8", rx=0.06)]
                  + [line(i, 0, i, -0.5, COL["tin"], 0.1) for i in range(5)],
    })
    add({
        "id": "vibration-motor", "name": "Vibration motor", "subtitle": "10 mm coin, 2-wire",
        "category": "motor", "tags": ["motor", "vibration", "haptic", "coin"],
        "designator": "M",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(1, 0, "-", 2, "gnd")],
        "shapes": [
            line(0, 0, 0.5, -0.3, "#d84040", 0.1),
            line(1, 0, 0.5, -0.3, "#1b1f25", 0.1),
            circle(0.5, -2.1, 1.95, "#3a3f47", "#22262c", sw=0.08),
            circle(0.5, -2.1, 0.7, "#8d949c", "#5c6269", sw=0.05),
        ],
        "label": {"text": "VIB M", "x": 0.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    })


# ===========================================================================
# Misc & mechanical
# ===========================================================================

def build_misc():
    add({
        "id": "buzzer-active-12mm", "name": "Buzzer active 12 mm", "subtitle": "self-oscillating, 5 V",
        "category": "misc", "tags": ["buzzer", "sound", "active", "alarm"],
        "designator": "BZ",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(2, 0, "-", 2, "gnd")],
        "shapes": [
            line(0, 0, 1.0, -0.2, COL["lead"], 0.1),
            line(2, 0, 1.0, -0.2, COL["lead"], 0.1),
            circle(1.0, -0.9, 2.3, COL["buzzer"], "#000000", sw=0.06),
            circle(1.0, -0.9, 0.32, "#3a3f47", "#22262c", sw=0.04),
            text(0.2, -2.5, "+", size=0.5, color="#c9ced6"),
        ],
        "label": {"text": "BUZZER", "x": 1.0, "y": 0.6, "size": 0.3, "color": "#9fb0c0"},
    })
    add({
        "id": "buzzer-passive-12mm", "name": "Buzzer passive 12 mm", "subtitle": "needs a drive signal",
        "category": "misc", "tags": ["buzzer", "sound", "passive", "tone"],
        "designator": "BZ",
        "footprint": {"cols": 3, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 1.0, -0.2, COL["lead"], 0.1),
            line(2, 0, 1.0, -0.2, COL["lead"], 0.1),
            circle(1.0, -0.9, 2.3, "#1f2429", "#0b0e12", sw=0.06),
            circle(1.0, -0.9, 1.5, "#2a3038", None),
            circle(1.0, -0.9, 0.32, "#3a3f47", "#22262c", sw=0.04),
        ],
        "label": {"text": "PASSIVE", "x": 1.0, "y": 0.6, "size": 0.3, "color": "#9fb0c0"},
    })
    add({
        "id": "speaker-8ohm", "name": "Speaker 8 Ω", "subtitle": "0.5 W, 28 mm",
        "category": "misc", "tags": ["speaker", "audio", "8ohm", "loudspeaker"],
        "designator": "LS",
        "footprint": {"cols": 6, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "signal"), pin(5, 0, "-", 2, "signal")],
        "shapes": [
            circle(2.5, -2.0, 5.2, "#2f343b", "#1a1d22", sw=0.08),
            circle(2.5, -2.0, 3.6, "#22262c", "#14171a", sw=0.06),
            circle(2.5, -2.0, 1.4, "#3a3f47", "#22262c", sw=0.05),
            line(0, 0, 0.6, -0.6, COL["lead"], 0.1),
            line(5, 0, 4.4, -0.6, COL["lead"], 0.1),
        ],
    })
    add({
        "id": "cr2032-holder", "name": "CR2032 holder", "subtitle": "20 mm coin cell",
        "category": "misc", "tags": ["battery", "cr2032", "coin cell", "holder"],
        "designator": "BT",
        "footprint": {"cols": 9, "rows": 5},
        "pins": [pin(0, 0, "-", 1, "gnd"), pin(0, 4, "-", 2, "gnd"),
                 pin(8, 2, "+", 3, "power")],
        "body": {"x": -0.5, "y": -0.5, "w": 9.5, "h": 5.5, "rx": 0.14,
                 "fill": "#22262c", "stroke": "#0e1116"},
        "shapes": [circle(4.0, 2.0, 3.9, "#c9ced6", "#8d949c", sw=0.08),
                   circle(4.0, 2.0, 3.2, "#dfe4ea", None),
                   text(4.0, 2.0, "CR2032", size=0.62, color="#5c6269")],
    })
    add({
        "id": "18650-holder", "name": "18650 holder", "subtitle": "single-cell, PCB mount",
        "category": "misc", "tags": ["battery", "18650", "lithium", "holder"],
        "designator": "BT",
        "footprint": {"cols": 26, "rows": 8},
        "pins": [pin(0, 0, "+", 1, "power"), pin(0, 7, "+", 2, "power"),
                 pin(25, 0, "-", 3, "gnd"), pin(25, 7, "-", 4, "gnd")],
        "body": {"x": -0.6, "y": -0.6, "w": 27.2, "h": 9.2, "rx": 0.2,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": [rect(1.0, 0.6, 24.0, 6.0, "#2f343b", "#14171a", rx=2.8),
                   text(13.0, 3.6, "18650", size=1.6, color="#6b737b")],
    })
    add({
        "id": "battery-clip-9v", "name": "9 V battery clip", "subtitle": "wire pads",
        "category": "misc", "tags": ["battery", "9v", "pp3", "clip"],
        "designator": "BT",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(1, 0, "-", 2, "gnd")],
        "shapes": [circle(0, 0, 0.34, "#d84040", "#8f2020", sw=0.05),
                   circle(1, 0, 0.34, "#3a3f47", "#14171a", sw=0.05),
                   text(0.5, -0.7, "9V", size=0.32, color="#9fb0c0")],
    })
    add({
        "id": "fuse-holder-5x20", "name": "Fuse holder 5×20", "subtitle": "PCB clips",
        "category": "misc", "tags": ["fuse", "protection", "holder"],
        "designator": "F",
        "footprint": {"cols": 9, "rows": 1},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(8, 0, "2", 2, "signal")],
        "shapes": [
            rect(0.5, -0.9, 7.0, 1.8, "#d8cfae", "#a89f7c", rx=0.85, opacity=0.85),
            rect(0.3, -0.7, 1.2, 1.4, COL["tin"], "#7f868e", rx=0.1),
            rect(6.5, -0.7, 1.2, 1.4, COL["tin"], "#7f868e", rx=0.1),
            line(1.5, 0, 6.5, 0, "#8d949c", 0.07),
        ],
        "label": {"text": "FUSE", "x": 4.0, "y": -1.2, "size": 0.32, "color": "#9fb0c0"},
    })
    add({
        "id": "mounting-hole-m3", "name": "Mounting hole M3", "subtitle": "3.2 mm clearance",
        "category": "misc", "tags": ["mechanical", "hole", "m3", "screw", "mount"],
        "designator": "H",
        "footprint": {"cols": 2, "rows": 2},
        "pins": [],
        "shapes": [
            circle(0.5, 0.5, 0.95, "none", "#8d949c", sw=0.1),
            circle(0.5, 0.5, 0.63, "#0b0e12", "#5c6269", sw=0.06),
        ],
    })
    add({
        "id": "test-point", "name": "Test point", "subtitle": "probe pad",
        "category": "misc", "tags": ["test", "probe", "pad", "debug"],
        "designator": "TP",
        "footprint": {"cols": 1, "rows": 1},
        "pins": [pin(0, 0, "TP", 1, "signal")],
        "shapes": [circle(0, 0, 0.42, "none", COL["copper"], sw=0.12),
                   circle(0, 0, 0.16, COL["copper"])],
    })
    add({
        "id": "solder-jumper", "name": "Solder jumper", "subtitle": "resizable bridge",
        "category": "misc", "tags": ["jumper", "bridge", "link", "solder"],
        "designator": "JP",
        "footprint": {"cols": 2, "rows": 1},
        "resize": {"axis": "cols", "min": 2, "max": 20},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(1, 0, "2", 2, "signal")],
        "shapes": [line(0, 0, 1, 0, COL["tin"], 0.3)],
    })
    add({
        "id": "heatsink-to220", "name": "Heatsink TO-220", "subtitle": "clip-on, 25 mm",
        "category": "misc", "tags": ["heatsink", "cooling", "thermal", "to-220"],
        "designator": "HS",
        "footprint": {"cols": 4, "rows": 4},
        "pins": [],
        "body": {"x": -0.3, "y": -0.3, "w": 4.0, "h": 4.0, "rx": 0.08,
                 "fill": COL["heatsink"], "stroke": "#5c6269"},
        "shapes": [rect(-0.15, -0.15 + i * 0.75, 3.7, 0.34, "#6f767e", None, rx=0.04)
                   for i in range(5)],
    })
    add({
        "id": "blank-module", "name": "Blank module", "subtitle": "generic placeholder, resizable",
        "category": "misc", "tags": ["blank", "generic", "custom", "placeholder"],
        "designator": "U",
        "footprint": {"cols": 4, "rows": 4},
        "resize": {"axis": "cols", "min": 1, "max": 40},
        "pins": [],
        "body": {"x": -0.4, "y": -0.4, "w": 4.8, "h": 4.8, "rx": 0.14,
                 "fill": "#2a3038", "stroke": "#4a525c"},
        "shapes": [],
        "label": {"text": "?", "x": 1.5, "y": 1.5, "size": 1.2, "color": "#7f868e"},
    })

    # -- power & mechanical --------------------------------------------------
    add({
        "id": "battery-holder-2xaa", "name": "AA holder, 2 cell", "subtitle": "PCB mount, 3 V",
        "category": "misc", "tags": ["battery", "aa", "holder", "2 cell", "3v"],
        "designator": "BT",
        "footprint": {"cols": 23, "rows": 12},
        "pins": [pin(0, 0, "+", 1, "power"), pin(0, 11, "-", 2, "gnd")],
        "body": {"x": -0.6, "y": -0.6, "w": 24.2, "h": 13.2, "rx": 0.2,
                 "fill": "#1a1d22", "stroke": "#0b0e12"},
        "shapes": [rect(1.0, 0.6, 20.6, 4.4, "#2f343b", "#14171a", rx=2.1),
                   rect(1.0, 6.4, 20.6, 4.4, "#2f343b", "#14171a", rx=2.1),
                   text(11.0, 5.7, "2 x AA", size=0.9, color="#6b737b")],
    })
    add({
        "id": "cr1220-holder", "name": "CR1220 holder", "subtitle": "12 mm coin cell",
        "category": "misc", "tags": ["battery", "cr1220", "coin cell", "holder", "rtc"],
        "designator": "BT",
        "footprint": {"cols": 6, "rows": 4},
        "pins": [pin(0, 0, "-", 1, "gnd"), pin(0, 3, "-", 2, "gnd"),
                 pin(5, 1, "+", 3, "power")],
        "body": {"x": -0.5, "y": -0.5, "w": 6.5, "h": 4.5, "rx": 0.12,
                 "fill": "#22262c", "stroke": "#0e1116"},
        "shapes": [circle(2.6, 1.5, 2.35, "#c9ced6", "#8d949c", sw=0.07),
                   circle(2.6, 1.5, 1.9, "#dfe4ea", None),
                   text(2.6, 1.5, "1220", size=0.5, color="#5c6269")],
    })
    add({
        "id": "heatsink-to247", "name": "Heatsink TO-247", "subtitle": "finned, 40 mm",
        "category": "misc", "tags": ["heatsink", "cooling", "thermal", "to-247", "to-3p"],
        "designator": "HS",
        "footprint": {"cols": 7, "rows": 6},
        "pins": [],
        "body": {"x": -0.3, "y": -0.3, "w": 7.0, "h": 6.0, "rx": 0.08,
                 "fill": COL["heatsink"], "stroke": "#5c6269"},
        "shapes": [rect(-0.15, -0.15 + i * 0.82, 6.7, 0.4, "#6f767e", None, rx=0.04)
                   for i in range(7)],
    })
    add({
        "id": "standoff-m3", "name": "Standoff M3", "subtitle": "brass spacer, 6 mm hex",
        "category": "misc", "tags": ["mechanical", "standoff", "spacer", "m3", "mount"],
        "designator": "H",
        "footprint": {"cols": 3, "rows": 3},
        "pins": [],
        "shapes": [
            polygon([(1.0, -0.2), (2.04, 0.4), (2.04, 1.6), (1.0, 2.2),
                     (-0.04, 1.6), (-0.04, 0.4)], COL["gold"], "#8a6f1a", sw=0.06),
            circle(1.0, 1.0, 0.6, "#0b0e12", "#8a6f1a", sw=0.05),
        ],
    })
    add({
        "id": "led-holder-5mm", "name": "LED holder 5 mm", "subtitle": "chrome bezel, panel",
        "category": "misc", "tags": ["led", "holder", "bezel", "panel", "5mm"],
        "designator": "H",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "A", 1, "power"), pin(1, 0, "K", 2, "gnd")],
        "shapes": [
            line(0, 0, 0.5, 0, COL["lead"], 0.1),
            line(1, 0, 0.5, 0, COL["lead"], 0.1),
            circle(0.5, 0, 1.15, COL["steel"], "#6f767e", sw=0.08),
            circle(0.5, 0, 0.62, "#14171a", "#3a4048", sw=0.05),
        ],
    })
    add({
        "id": "microphone-electret", "name": "Electret microphone", "subtitle": "9.7 mm capsule",
        "category": "misc", "tags": ["microphone", "electret", "audio", "capsule"],
        "designator": "MK",
        "footprint": {"cols": 2, "rows": 1},
        "pins": [pin(0, 0, "+", 1, "power"), pin(1, 0, "-", 2, "gnd")],
        "shapes": [
            line(0, 0, 0.5, -0.2, COL["lead"], 0.09),
            line(1, 0, 0.5, -0.2, COL["lead"], 0.09),
            circle(0.5, -2.1, 1.9, "#c9ced6", "#8d949c", sw=0.08),
            circle(0.5, -2.1, 1.5, "#3a3f47", None),
            circle(0.5, -2.1, 0.5, "#1a1d22", None),
        ],
        "label": {"text": "MIC", "x": 0.5, "y": 0.44, "size": 0.28, "color": "#9fb0c0"},
    })
    add({
        "id": "fan-40mm", "name": "Fan 40 mm", "subtitle": "12 V DC, 2-wire",
        "category": "misc", "tags": ["fan", "cooling", "40mm", "12v", "airflow"],
        "designator": "FAN",
        "footprint": {"cols": 16, "rows": 16},
        "pins": [pin(0, 0, "+", 1, "power"), pin(0, 15, "-", 2, "gnd")],
        "body": {"x": -0.5, "y": -0.5, "w": 16.0, "h": 16.0, "rx": 0.6,
                 "fill": "#22262c", "stroke": "#0e1116"},
        "shapes": [circle(7.5, 7.5, 7.2, "#1a1d22", "#3a4048", sw=0.1),
                   circle(7.5, 7.5, 2.2, "#3a3f47", "#22262c", sw=0.08)]
                  + [circle(1.0 + 13.0 * (i % 2), 1.0 + 13.0 * (i // 2), 0.75,
                            "none", "#5c6269", sw=0.14) for i in range(4)],
    })

    # -- documentation aids: these carry no pins, they annotate the layout ----
    add({
        "id": "note-label", "name": "Note / text label", "subtitle": "annotation, resizable",
        "category": "misc", "tags": ["note", "label", "text", "annotation", "documentation"],
        "designator": "NOTE",
        "footprint": {"cols": 6, "rows": 2},
        "resize": {"axis": "cols", "min": 2, "max": 40},
        "pins": [],
        "body": {"x": -0.3, "y": -0.3, "w": 5.6, "h": 1.6, "rx": 0.12,
                 "fill": "#1f2733", "stroke": "#3d5a80", "opacity": 0.9},
        "shapes": [],
        "label": {"text": "note", "x": 2.5, "y": 0.5, "size": 0.6, "color": "#9dc1e8"},
    })
    add({
        "id": "keepout-area", "name": "Keep-out area", "subtitle": "reserved space, resizable",
        "category": "misc", "tags": ["keepout", "reserved", "clearance", "area", "mechanical"],
        "designator": "KO",
        "footprint": {"cols": 4, "rows": 4},
        "resize": {"axis": "cols", "min": 2, "max": 40},
        "pins": [],
        "body": {"x": -0.3, "y": -0.3, "w": 3.6, "h": 3.6, "rx": 0.08,
                 "fill": "#3a2020", "stroke": "#8f4040", "opacity": 0.55},
        "shapes": [line(-0.3, -0.3, 3.3, 3.3, "#8f4040", 0.08),
                   line(3.3, -0.3, -0.3, 3.3, "#8f4040", 0.08)],
    })
    add({
        "id": "track-cut", "name": "Track cut", "subtitle": "stripboard break marker",
        "category": "misc", "tags": ["stripboard", "cut", "break", "veroboard", "track"],
        "designator": "X",
        "footprint": {"cols": 1, "rows": 1},
        "pins": [],
        "shapes": [circle(0, 0, 0.44, "none", "#e04a3a", sw=0.12),
                   line(-0.3, -0.3, 0.3, 0.3, "#e04a3a", 0.12),
                   line(0.3, -0.3, -0.3, 0.3, "#e04a3a", 0.12)],
    })
    add({
        "id": "wire-link", "name": "Wire link marker", "subtitle": "single insulated jumper",
        "category": "misc", "tags": ["link", "jumper", "bridge", "wire"],
        "designator": "LK",
        "footprint": {"cols": 3, "rows": 1},
        "resize": {"axis": "cols", "min": 2, "max": 30},
        "pins": [pin(0, 0, "1", 1, "signal"), pin(2, 0, "2", 2, "signal")],
        "shapes": [
            line(0, 0, 2, 0, "#7f868e", 0.14),
            rect(0.35, -0.14, 1.3, 0.28, "#e8c72c", "#a89020", rx=0.14),
        ],
        "label": {"text": "LK", "x": 1.0, "y": -0.42, "size": 0.26, "color": "#9fb0c0"},
    })


# ===========================================================================
# Writing
# ===========================================================================

BUILDERS = [build_mcu, build_ic, build_power, build_sensor, build_display,
            build_passive, build_discrete, build_connector, build_comms,
            build_motor, build_misc]


def write_modules():
    known_cats = {c["id"] for c in CATEGORIES}
    seen: dict[str, str] = {}
    written = []

    for mod in BUILT:
        mid, cat = mod["id"], mod["category"]
        if cat not in known_cats:
            raise SystemExit(f"module {mid}: unknown category {cat!r}")
        if mid in seen:
            raise SystemExit(f"duplicate module id {mid!r}")
        seen[mid] = cat

        rel = f"{cat}/{mid}.json"
        out = MODULES / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {"$schema": "../_schema/module.schema.json", **mod}
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        written.append(rel)

    return written


def write_bundle():
    """Inline every listed module into modules/catalog.json.

    With several hundred parts, fetching one file each would mean several
    hundred round trips before the palette can draw.  The bundle is a pure
    build artifact: the per-category .json files stay the source of truth, and
    the app falls back to fetching them individually if this file is missing.
    One module per line keeps the diff readable without paying for indentation.
    """
    index = json.loads((MODULES / "index.json").read_text(encoding="utf-8"))
    compact = {"ensure_ascii": False, "separators": (",", ":")}

    entries = []
    for rel in index["modules"]:
        data = json.loads((MODULES / rel).read_text(encoding="utf-8"))
        data.pop("$schema", None)
        entries.append(f"{json.dumps(rel)}:{json.dumps(data, **compact)}")

    comment = ("Generated by tools/generate_catalog.py — do not hand-edit. Every "
               "module from index.json, inlined so the app boots in a single "
               "request. Re-run the generator after changing any module file.")
    body = (
        "{\n"
        f'"$comment":{json.dumps(comment)},\n'
        f'"pitchMm":{json.dumps(index["pitchMm"])},\n'
        f'"categories":{json.dumps(index["categories"], **compact)},\n'
        '"definitions":{\n'
        + ",\n".join(entries)
        + "\n}\n}\n"
    )
    (MODULES / "catalog.json").write_text(body, encoding="utf-8")
    return len(entries)


def write_index(paths=None):
    """Rebuild modules/index.json by scanning the tree (authoritative)."""
    found = []
    for cat in CATEGORIES:
        d = MODULES / cat["id"]
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            found.append(f"{cat['id']}/{f.name}")

    index = {
        "$comment": "Generated by tools/generate_catalog.py. Lists every module the "
                    "app should load. Add a file here (or re-run the script) to "
                    "publish a new module.",
        "pitchMm": 2.54,
        "categories": CATEGORIES,
        "modules": found,
    }
    (MODULES / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", action="store_true",
                    help="only rebuild modules/index.json from the files on disk")
    args = ap.parse_args()

    if args.index:
        found = write_index()
        bundled = write_bundle()
        print(f"index.json rebuilt: {len(found)} modules, catalog.json: {bundled}")
        return

    for b in BUILDERS:
        b()
    written = write_modules()
    found = write_index(written)
    write_bundle()
    by_cat: dict[str, int] = {}
    for rel in found:
        by_cat[rel.split("/")[0]] = by_cat.get(rel.split("/")[0], 0) + 1
    print(f"wrote {len(written)} module files, index lists {len(found)}")
    for c in CATEGORIES:
        print(f"  {c['id']:<10} {by_cat.get(c['id'], 0):>4}")


if __name__ == "__main__":
    main()

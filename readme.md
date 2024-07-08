# Product specification

Smart BMS product is thing which helps to control charging process of LiFePo4 BLE BMS connected battery.

## Hardware setup
- ESP32 4Mb Flash
    - ~1.9Mb for OTA app
    - ~256Kb for Data storage
- PIN 33 for Relay (charging control)
- PIN 0 for OTA/PROG 
- WIFI for OTA
- BLE for communication with BMS over BLE

## Key features
- OTA over WIFI server
    - WiFi creds
    - Firmware
    - BMS settings
- Smart BMS Charge controller app
    - Charging timeout (3-4 hours)
    - Charging logic:
        - initial charge to max 100%
        - after full charge fall back to min charge level before charging to 100% again


## Dependencies
- Prerequisites
    ```
    sudo apt install esptool
    sudo pip3 install rshell adafruit-ampy
    ```
    
    - For mpy-cross tool to produce frozen bytecode 
        ```    
        sudo apt-get install build-essential libffi-dev git pkg-config
        sudo apt-get install gcc-arm-none-eabi libnewlib-arm-none-eabi
        ```
        - download snapshot of micropython https://micropython.org/resources/source/micropython-1.23.0.tar.xz or `git clone https://github.com/micropython/micropython.git`
        - cd micropython/mpy-cross
        - make
        - sudo cp build/mpy-cross /usr/bin
    - For git management
        ```
        sudo apt instgall gh jq
        ```

- Micropython Setup (https://micropython.org/download/ESP32_GENERIC/)
    ```
    esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
    esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20240602-v1.23.0.bin
    ```

## Resetting git history
```
rm -rf .git
git init --initial-branch=main
git init -b main
git add .
git commit -m initial
git remote add origin git@github.com:torimos/diy.smart-bms.git
git push -u --force origin main

```

## Deploy scripts into ESP32
- Bulk upload
```
rshell -p /dev/ttyUSB0 cp src/*.py /pyboard
```

## Run scripts without upload
```
ampy --port /dev/ttyUSB0 run demo.py

```

## Connect to device
```
python -m serial.tools.miniterm --raw /dev/ttyUSB0 115200

```

## Resources
- https://github.com/micropython/micropython/blob/master/examples/bluetooth/
import time
import gc
import wifimgr
import ota

from bmsinfo import BMSInfo
from machine import Pin

#TARGET = "E3:67:8D:DA:79:FA"
TARGET = "30:AE:A4:DC:CD:B2" # fake

CHARGE_TIMEOUT_SEC = 2 * 60 * 60
SYNC_INTERVAL = 5

led = Pin(19, Pin.OUT) # 2-devkit, 19-ttgo
relay = Pin(33, Pin.OUT)

def enable_charging(flag):
    relay.value(not flag)

enable_charging(False)

bms_info = BMSInfo()
statTime = time.time()
syncTime = -SYNC_INTERVAL

def wifi_init():
    wlan = wifimgr.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        while True:
            pass  # you shall not pass :D

def blink(ntimes, delay):
    for i in range(ntimes):
        led.value(0)
        time.sleep(delay)
        led.value(1)
        time.sleep(delay)


def retry(callback, retryCount):
    retry_iteration = 0
    while retry_iteration < retryCount:
        if callback():
            break
        else:
            retry_iteration += 1
    return retry_iteration < retryCount

def sync():
    if bms_info.update():
        bms_info.debug()
        enable_charging(bms_info.charging_enabled)
        if (bms_info.charging_enabled):
            blink(1, 0.2)
        else:
            blink(4, 0.1)
        bms_info.disconnect()
        return True
    return False

def connect():
    if bms_info.connect_by_address(TARGET):
        if retry(sync, 5) == False:
            print("Sync Failed - Update Error")
            blink(15, 0.1)  
        return True
    return False


print("WIFI Init")
wifi_init()
print("Starting OTA Update")
ota.ota_update()

while(True):
    if ((time.time()-statTime) > CHARGE_TIMEOUT_SEC):
        print("Charge timeout has been reached!")
        enable_charging(False)
        break
    
    if ((time.time()-syncTime) > SYNC_INTERVAL):
        print("Sync in progress...")
        try:
            led.value(1)
            if retry(connect, 3) == False:
                print("Failed to connect - device not available")
                blink(10, 0.1)
        except OSError as err:
            print("ERR", err)
            blink(3, 0.5)
            pass
        led.value(0)
        gc.collect()
        syncTime = time.time()
        
    time.sleep(0.2)

print("Charge control rutine finished. Restart device .")
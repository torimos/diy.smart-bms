import time
import gc
from bmsinfo import BMSInfo
from machine import Pin

TARGET = "E3:67:8D:DA:79:FA"
#TARGET = "30:AE:A4:DC:CD:B2"

CHARGE_TIMEOUT_SEC = 2 * 60 * 60
SYNC_INTERVAL = 10

led = Pin(2, Pin.OUT)
relay = Pin(33, Pin.OUT)

def enable_charging(flag):
    relay.value(not flag)

enable_charging(False)

bms_info = BMSInfo()
statTime = time.time()
syncTime = -SYNC_INTERVAL

def blink(ntimes, delay):
    for i in range(ntimes):
        led.value(0)
        time.sleep(delay)
        led.value(1)
        time.sleep(delay)

while(True):
    if ((time.time()-statTime) > CHARGE_TIMEOUT_SEC):
        print("Charge timeout has been reached!")
        enable_charging(False)
        break
    
    if ((time.time()-syncTime) > SYNC_INTERVAL):
        print("Sync...")
        try:
            led.value(1)
            if bms_info.connect_by_address(TARGET):
                bms_info.update()
                bms_info.debug()
                enable_charging(bms_info.charging_enabled)
                if (bms_info.charging_enabled):
                    blink(1, 0.2)
                else:
                    blink(4, 0.1)
                bms_info.disconnect()
            else:
                print("Sync Failed - No Device")
                blink(10, 0.1)
        except:
            blink(3, 0.5)
            pass
        led.value(0)
        gc.collect()
        syncTime = time.time()
        
    time.sleep(0.2)

print("Charge control rutine finished. Restart device .")
import gc
import wifimgr
import ota

def wifi_init():
    wlan = wifimgr.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        while True:
            pass  # you shall not pass :D

gc.collect()
print("Startup",gc.mem_free())
wifi_init()
ota.ota_update()

gc.collect()
print("Ready!", gc.mem_free())

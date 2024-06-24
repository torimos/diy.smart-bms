
import time
from bmsinfo import BMSInfo
import gc

print("Demo BMS v1")
gc.collect()
print(gc.mem_free())
bms_info = BMSInfo()
if bms_info.connect("12V100A00392"):
    gc.collect()
    print(gc.mem_free())
    bms_info.update()
    gc.collect()
    print(gc.mem_free())
    bms_info.debug()
    gc.collect()
    print(gc.mem_free())
    bms_info.disconnect()
gc.collect()
print(gc.mem_free())

print("Done!")

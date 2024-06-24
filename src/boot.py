# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)

import sys
sys.path.append("/frozen")

import gc
gc.collect()

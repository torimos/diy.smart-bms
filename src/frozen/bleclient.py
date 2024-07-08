import bluetooth
import time
from micropython import const


_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_NOTIFY = const(18)

_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

class BLECharacteristic:
    def __init__(self, service, uuid, handle):
        self._service = service
        self._uuid = uuid
        self._handle = handle

    def get_uuid(self) -> bluetooth.BLE:
        return self._uuid

    def write(self, data):
        self._service._write(self._handle, data)

class BLEService:
    def __init__(self, ble, uuid, conn_handle, start_handle, end_handle):
        self._ble = ble
        self._uuid = uuid
        self._conn_handle = conn_handle
        self._start_handle = start_handle
        self._end_handle = end_handle
        self._characteristics = []
    
    def get_uuid(self):
        return self._uuid

    def has_handle(self, handle) -> bool:
        return self._start_handle <= handle <= self._end_handle 
    
    def append_characteristic(self, characteristic: BLECharacteristic):
        self._characteristics.append(characteristic)
    
    def get_characteristic(self, uuid) -> BLECharacteristic:
        _uuid = bluetooth.UUID(uuid)
        for ch in self._characteristics:
            if (ch.get_uuid() == _uuid):
                return ch
        return None
    
    def _write(self, handle, data):
        self._ble.gattc_write(self._conn_handle, handle, data)

class BLEClient:

    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._reset()

    def _reset(self):
        self._device_name = None
        self._device_address = None
        self._device_address_type = None

        self._conn_handle = None

        self._notify_callback = None

        self._services = []
        self._discovery_done = False

    def _decode_field(self, payload, adv_type):
        i = 0
        result = []
        while i + 1 < len(payload):
            if payload[i + 1] == adv_type:
                result.append(payload[i + 2 : i + payload[i] + 1])
            i += 1 + payload[i]
        return result

    def _decode_name(self, payload):
        n = self._decode_field(payload, 0x9)
        return str(n[0], "utf-8") if n else ""

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            # A single scan result.
            addr_type, addr, connectable, rssi, adv_data = data
            name = self._decode_name(adv_data)
            if self._device_name == name:
                self._device_address = ':'.join(['%02X' % i for i in addr])
                self._device_address_type = addr_type
                self._ble.gap_scan(None)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            # Connect successful.
            conn_handle, addr_type, addr = data
            # print("_IRQ_PERIPHERAL_CONNECT", conn_handle, ['%02X' % a for a in addr])
            self._conn_handle = conn_handle
            self._ble.gattc_discover_services(conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, addr_type, addr = data
            # print("_IRQ_PERIPHERAL_DISCONNECT", conn_handle, ['%02X' % a for a in addr])
            self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            # print("_IRQ_GATTC_SERVICE_RESULT", conn_handle, uuid, '%02X' % start_handle, '%02X' % end_handle)
            self._services.append(BLEService(self._ble, bluetooth.UUID(uuid), self._conn_handle, start_handle, end_handle))

        elif event == _IRQ_GATTC_SERVICE_DONE:
            conn_handle, status = data
            # print("_IRQ_GATTC_SERVICE_DONE", conn_handle, status)
            if status == 0:
                self._ble.gattc_discover_characteristics(self._conn_handle, 0x1, 0xFFFF)

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, end_handle, value_handle, properties, uuid = data
            # print("_IRQ_GATTC_CHARACTERISTIC_RESULT", uuid, end_handle, value_handle, properties)
            for svc in self._services:
                if svc.has_handle(value_handle):
                    svc.append_characteristic(BLECharacteristic(svc, bluetooth.UUID(uuid), value_handle))
                    break

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            conn_handle, status = data
            # print("_IRQ_GATTC_CHARACTERISTIC_DONE", conn_handle, status)
            self._discovery_done = status == 0

        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            if self._notify_callback:
                self._notify_callback(value_handle, notify_data)


    def scan_connect(self, name, scan_timeout = 1000, active = True):
        self._device_name = name
        self._ble.gap_scan(scan_timeout, 30000, 30000, True)
        time.sleep_ms(scan_timeout)
        if self._device_address != None:
            return self.connect(self._device_address, self._device_address_type, scan_timeout, active)
        return None

    def connect(self, address, address_ype, scan_timeout = 1000, active = True):
        addr_bytes = bytes(int(b, 16) for b in address.split(':'))
        self._ble.gap_connect(address_ype, addr_bytes, scan_timeout)
        t = time.time()*1000
        if active:
            while not self.is_connected() and (time.time()*1000-t) < scan_timeout:
                time.sleep_ms(500)
            return self.is_connected()
        return None
    
    def disconnect(self):
        if self.is_connected():
            self._ble.gap_disconnect(self._conn_handle)
        self._reset()

    def is_connected(self):
        return (
            self._conn_handle is not None
            and self._discovery_done
        )
    
    def get_device_address(self):
        return self._device_address

    def on_notify(self, callback):
        self._notify_callback = callback

    def get_service(self, uuid) -> BLEService:
        _uuid = bluetooth.UUID(uuid)
        for svc in self._services:
            if (svc.get_uuid() == _uuid):
                return svc
        return None
from bleclient import BLEClient, BLECharacteristic
import time

def _two_ints_into16(high_byte, low_byte):
    return (high_byte << 8) | low_byte

class BMSInfoRequest:
    def __init__(self, tx: BLECharacteristic):
        self._tx = tx

    def _reset(self):
        self.packetstate = 0 # 0 - empty, 1 - first half of packet received, 2 - second half of partial packet received
        self.packetbuff = [0x0] * 40
        self.packetSize = 0
        self.previousDataSize = 0

    def process(self, data):
        dataSize = len(data)
        #print("Notification from", '%02X' % handle, dataSize, ['%02X' % b for b in data])

        if data[0] == 0xdd and data[dataSize - 1] == 0x77: # probably got full packet
            self.packetstate = 2
            for i in range(dataSize):
                self.packetbuff[i] = data[i]
        
        elif data[0] == 0xdd and self.packetstate == 0:  # probably got 1st half of packet
            self.packetstate = 1
            self.previousDataSize = dataSize
            for i in range(dataSize):
                self.packetbuff[i] = data[i]

        elif data[dataSize - 1] == 0x77 and self.packetstate == 1:  # probably got 2nd half of the partial packet
            self.packetstate = 2
            for i in range(dataSize):
                self.packetbuff[i + self.previousDataSize] = data[i]

        if self.packetstate == 2:  # got full packet
            self.packetSize = dataSize + self.previousDataSize
            self.packetstate = 0
        
    def _wait_for(self, expr, timeout = 1000, interval = 100):
        t = time.time()*1000
        while expr() and (time.time()-t) < timeout:
            time.sleep_ms(interval)
        return (time.time()*1000-t)<timeout

    def send(self, payload):
        self._reset()
        self._tx.write(bytes(payload))
        if self._wait_for(lambda: self.packetSize == 0):
            return  self.packetbuff[: self.packetSize]
        return None

class BMSInfo:
    # VoltPolska 100/150Ah battery BMS BLEInfo
    _ENV_BMS_SERVICE_UUID = 0xff00 #"0000ff00-0000-1000-8000-00805f9b34fb"
    _ENV_BMS_SERVICE_RX_UUID = 0xff01 #"0000ff01-0000-1000-8000-00805f9b34fb"
    _ENV_BMS_SERVICE_TX_UUID = 0xff02 #"0000ff02-0000-1000-8000-00805f9b34fb"

    _ENV_BMS_BASIC_INFO_REQ = [0xdd, 0xa5, 0x3, 0x0, 0xff, 0xfd, 0x77]
    _ENV_BMS_CELLS_INFO_REQ = [0xdd, 0xa5, 0x4, 0x0, 0xff, 0xfc, 0x77]

    def __init__(self):
        self._req = None
        self._client = None

        self.voltage = 0.0
        self.current = 0.0
        self.remaining_capacity = 0.0
        self.nominal_capacity = 0.0
        self.charge_level = 0.0
        self.cycles = 0
        self.prod_date = 0
        self.low_balance = 0
        self.high_balance = 0
        self.protection_status = 0
        self.soft_ver = 0
        self.rem_cap = 0
        self.charging_enabled = False
        self.discharging_enabled = False
        self.cells_count = 0
        self.num_temp = 0
        self.temperatures = []
        self.cells_voltage = []

    def connect(self, name):
        self._client = BLEClient()
        if self._client.scan_connect(name):
            svc = self._client.get_service(BMSInfo._ENV_BMS_SERVICE_UUID)
            if svc != None:
                tx = svc.get_characteristic(BMSInfo._ENV_BMS_SERVICE_TX_UUID)
                if tx != None:
                    self._req = BMSInfoRequest(tx)
                    self._client.on_notify(lambda _, data: self._req.process(data))
                return True
        return False


    def connect_by_address(self, address, type = 0, timeout=5000):
        self._client = BLEClient()
        if self._client.connect(address, type, timeout):
            svc = self._client.get_service(BMSInfo._ENV_BMS_SERVICE_UUID)
            if svc != None:
                tx = svc.get_characteristic(BMSInfo._ENV_BMS_SERVICE_TX_UUID)
                if tx != None:
                    self._req = BMSInfoRequest(tx)
                    self._client.on_notify(lambda _, data: self._req.process(data))
                    return True
                else:
                    print("ERR: TX characteristics not found:", BMSInfo._ENV_BMS_SERVICE_TX_UUID)
            else:
                print("ERR: Service not found", BMSInfo._ENV_BMS_SERVICE_UUID)
        return False

    def disconnect(self):
        if self._client != None:
            self._client.disconnect()
    
    def update(self):
        if self._req != None:
            resp1 = self._req.send(BMSInfo._ENV_BMS_BASIC_INFO_REQ)
            if resp1 != None:
                resp2 = self._req.send(BMSInfo._ENV_BMS_CELLS_INFO_REQ)

                data = resp1[4:]
                self.voltage = float(_two_ints_into16(data[0], data[1])) / 100.0
                self.current = float(_two_ints_into16(data[2], data[3])) / 100.0
                self.remaining_capacity = float(_two_ints_into16(data[4], data[5])) / 100.0
                self.nominal_capacity = float(_two_ints_into16(data[6], data[7])) / 100.0
                self.charge_level = 100.0 * self.remaining_capacity / self.nominal_capacity
                self.cycles = _two_ints_into16(data[8], data[9])
                self.prod_date = _two_ints_into16(data[10], data[11])
                self.low_balance = _two_ints_into16(data[12], data[13])
                self.high_balance = _two_ints_into16(data[14], data[15])
                self.protection_status = _two_ints_into16(data[16], data[17])
                self.soft_ver = data[18]
                self.rem_cap = data[19]
                self.charging_enabled = (data[20] & 0x01) != 0
                self.discharging_enabled = (data[20] & 0x02) != 0
                self.cells_count = data[21]
                self.num_temp = data[22]
                self.temperatures = [0] * self.num_temp

                for i in range(self.num_temp):
                    self.temperatures[i] = (float(_two_ints_into16(data[23 + i * 2], data[23 + i * 2 + 1])) - 2731) / 10.0

                if resp2 != None:
                    data = resp2[4:]
                    num_cells = resp2[3] // 2
                    self.cells_voltage = [0.0] * num_cells

                    for i in range(num_cells):
                        high_byte = data[i * 2]
                        low_byte = data[i * 2 + 1]
                        self.cells_voltage[i] = float(_two_ints_into16(high_byte, low_byte)) / 1000.0  # Resolution 1 mV

                return True
        return False

    def debug(self):
        print(f"voltage: {self.voltage:.3f}")
        print(f"current: {self.current:.3f}")
        print(f"charge_level: {self.charge_level:.1f}")
        print(f"remaining_capacity: {self.remaining_capacity:.3f}")
        print(f"nominal_capacity: {self.nominal_capacity:.3f}")
        print(f"cycles: {self.cycles}")
        print(f"prod_date: {self.prod_date}")
        print(f"low_balance: {self.low_balance}")
        print(f"high_balance: {self.high_balance}")
        print(f"protection_status: {self.protection_status}")
        print(f"soft_ver: {self.soft_ver}")
        print(f"rem_cap: {self.rem_cap}")
        print(f"charging_enabled: {int(self.charging_enabled)}")
        print(f"discharging_enabled: {int(self.discharging_enabled)}")
        print(f"cells_count: {self.cells_count}")
        print(f"num_temp: {self.num_temp}")
        if self.temperatures:
            print(f"temp0: {self.temperatures[0]:.3f}")
        for i in range(self.cells_count):
            print(f"cell[{i}]: {self.cells_voltage[i]:.3f}")
        print()
    
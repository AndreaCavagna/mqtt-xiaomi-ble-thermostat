from bluepy.btle import Scanner, DefaultDelegate

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            #print("Discovered device", dev.addr)
            pass
        elif isNewData:
            #print("Received new data from", dev.addr)
            pass


class BluepyCustomScanner:

    scanTime = 10 ## DEFAULT SCANNING TIME IN SECONDS

    def __init__(self):
        self.scanner = Scanner().withDelegate(ScanDelegate())


    def scanAll(self, scanTime = scanTime, printScan = False):
        devices = self.scanner.scan(float(scanTime))
        if printScan:
            for dev in devices:
                print("Device {} ({}), RSSI={} dB".format(dev.addr, dev.addrType, dev.rssi))
                for (adtype, desc, value) in dev.getScanData():
                    print("  {} = {}".format(desc, value))
                    '''with open('bluepyscanlog.txt', 'a') as the_file:
                        the_file.write("{}={}\n".format(desc, value))'''
        return devices

    def scanSingle(self, mac, scanTime = scanTime, printScan = False):
        devices = self.scanner.scan(float(scanTime))
        for dev in devices:
            if str(mac).capitalize() == str(dev.addr).capitalize():
                if printScan:
                    print("Device {} ({}), RSSI={} dB".format(dev.addr, dev.addrType, dev.rssi))
                    for (adtype, desc, value) in dev.getScanData():
                        print("  {} = {}".format(desc, value))
                        '''with open('bluepyscanlog.txt', 'a') as the_file:
                            the_file.write("{}={}\n".format(desc, value))'''
                return dev
        return False



    def getRSSI(self, mac, scanTime = scanTime):
        device = self.scanSingle(mac, scanTime, False)
        if not device:
            return False
        return str(device.rssi)




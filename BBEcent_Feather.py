

import time
import board
from analogio import AnalogIn
import digitalio
#import adafruit_ds18x20
#from adafruit_onewire.bus import OneWireBus
import busio
import countio


uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=0)

# intialize OneWire bus for Temp Sensors
#ow_bus = OneWireBus(board.D5)
#devices = ow_bus.scan()

# get pressure sensor voltage
def get_voltage(pin):
    min = 1.76
    max = 3.3
    offset = 0.35
    
    #return (pin * 3.3) / 65536.0
    return (pin - min)/(max - min)/65536.0 - offset

def get_ml(pre, post):
    return (pre - post) / 2.038




#flow sensor
# 2.038 counts per mililiter

initial_time = time.monotonic()

#Flowmeter 1 - Post OPV
f1pin_counter = countio.Counter(board.D10)
f1pin_counter.reset()
f1count = 0

#Flowmeter 2 - Pre Pump
f2pin_counter = countio.Counter(board.D11)
f2pin_counter.reset()
f2count = 0


#Pressure

Panalog_in = AnalogIn(board.A5)



#150PSI = 10.34 BAR 200 PSI = 13.79 BAR
Pmax = 10.34 # max expected output in Bar pressure.
Vadjustment = 0 #





# inline = adafruit_ds18x20.DS18X20(ow_bus, devices[0])
# grphead = adafruit_ds18x20.DS18X20(ow_bus, devices[1])
# outlet = adafruit_ds18x20.DS18X20(ow_bus, devices[2])
# inline.resolution = 9
# grphead.resolution = 9
# outlet.resolution = 9


while True:
    current_time = time.monotonic()
    time_stamp = current_time - initial_time
    print("Seconds since current data log started:", int(time_stamp))
    # temp1 = inline.temperature
    # temp2 = grphead.temperature
    # temp3 = outlet.temperature
    # print("Inline:", temp1)
    # print("Group Head:", temp2)
    # print("Outlet:",temp3)

    f1count = f1pin_counter.count
    f2count = f2pin_counter.count

    print("Pump Volume:", f2count / 2.038, "OPV Volume:" , f1count / 2.038)
    vol = '{0:.2f}'.format(get_ml(f2count, f1count))
    flow = '{0:.2f}'.format(get_ml(f2count,f1count) / (time_stamp - initial_time)) #formula needs fixing
    print("The flow is: {} ml/sec".format(flow))

    V = get_voltage(Panalog_in.value) - Vadjustment
    print(V)
    P = '{0:.2f}'.format(((V * Pmax) * 3.3))
    print("Pressure:", P)
    message = f"<{time_stamp},{vol},{flow},{P}>"
    uart.write(bytes(message, "ascii"))
    print(message)

    time.sleep(0.25)




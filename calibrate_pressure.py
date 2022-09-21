

import time
import board
from analogio import AnalogIn
import digitalio
import neopixel

#--------------Pixel Colors --------#
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 0)
CYAN = (0, 255, 255)
PURPLE = (180, 0, 255)
BLACK = (0, 0, 0)


pixel[0] = WHITE



#Pressure Sensor Pin
Panalog_in = AnalogIn(board.A3)




# get pressure sensor voltage
def get_voltage(pin):
    return (pin.value * 3.3) / 65536

#get pressure reading
def get_pressure(pin): 
    #Pressure = Pressure_max x (Vout - min)/(max - min)
    #150PSI = 10.34 BAR 200 PSI = 13.79 BAR
    Pmax = 10.34 # max expected output in Bar pressure.
    min = 1.37 #minimum voltage
    max = 3.3 #maximum voltage
    volt_rdg = (pin.value * 3.3) / 65536
    return (Pmax * (volt_rdg - min)/(max - min))
    





#Pressure

Panalog_in = AnalogIn(board.A3)





while True:
    current_time = time.monotonic()
    
    V = get_voltage(Panalog_in)

    P = '{0:.2f}'.format(get_pressure(Panalog_in))
    print("Voltage:",V, "Pressure:", P)
    print((V,float(P)))
    

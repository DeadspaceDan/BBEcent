import time
import board
from analogio import AnalogIn
import countio
import neopixel

#setup neopixel
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



#If code is up to date it should turn purple then Green
pixel[0] = PURPLE

# Setup Flowmeters
# 2.058 counts per mililiter

# Flowmeter 1 - Pre Pump
f1pin_counter = countio.Counter(board.D13)
f1pin_counter.reset()
f1count = f1pin_counter.count

now = time.monotonic()
last_loop_count = f1count
last_time_polled = now


while True:
    time.sleep(.5)
    now = time.monotonic()
    nowcount = f1pin_counter.count
    elapsed_time = now - last_time_polled
    elapsed_count = nowcount - last_loop_count
    pulse = elapsed_count / elapsed_time
    ml_sec = pulse / 2.058
    last_time_polled = now
    last_loop_count = nowcount
    pixel[0] = GREEN
    print((ml_sec,))




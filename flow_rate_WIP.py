import time
import board
from analogio import AnalogIn
import countio
import neopixel


class TimeManager:
    def __init__(self, period):
        self.lastCheckedTime = None
        self.period = period
        self.lastCheckedTime = time.monotonic()

    def goNow(self):
        self.current_time = time.monotonic()
        self.elapsed_time = self.current_time - self.lastCheckedTime
        return self.elapsed_time > self.period

    def reset(self):
        self.lastCheckedTime = self.current_time


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


last_loop_count = f1count



tm = TimeManager(0.5)
tm2 = TimeManager(0.125)

while True:
    if tm.goNow():
        nowcount = f1pin_counter.count
        elapsed_count = nowcount - last_loop_count
        pulse = elapsed_count / tm.elapsed_time
        ml_sec = pulse / 2.058
        last_loop_count = nowcount
        pixel[0] = GREEN
        print((ml_sec,))
        tm.reset()




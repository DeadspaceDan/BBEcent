# SPDX-FileCopyrightText: 2022 Dan O'Mara - mechlabs.ai
#
# SPDX-License-Identifier: MIT

import time
import json
import gc
import board
import adafruit_pyportal
import busio
import displayio
import digitalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import bitmap_label as label
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.rect import Rect
from adafruit_button import Button
import adafruit_touchscreen

pyportal = adafruit_pyportal.PyPortal()
display = board.DISPLAY
display.rotation = 180

#-------- Serial Communication------#
uart = busio.UART(board.SDA, board.SCL, baudrate=9600, timeout=0)

# Wait for the beginning of a message.
message_started = False



TITLE = "BBEcent"
VERSION = "1.0"

print(TITLE, "Version: ", VERSION)

display_group = displayio.Group()
board.DISPLAY.show(display_group)

PROFILE_SIZE = 2  # plot thickness
GRID_SIZE = 1
GRID_STYLE = 3
AXIS_SIZE = 1

BLACK = 0x0
BLUE = 0x2020FF
GREEN = 0x00FF55
RED = 0xFF0000
YELLOW = 0xFFFF00

WIDTH = board.DISPLAY.width
HEIGHT = board.DISPLAY.height

palette = displayio.Palette(5)
palette[0] = BLACK
palette[1] = GREEN
palette[2] = BLUE
palette[3] = RED
palette[4] = YELLOW

palette.make_transparent(0)

BACKGROUND_COLOR = 0
PROFILE_COLOR = 1
GRID_COLOR = 2
TEMP_COLOR = 3
AXIS_COLOR = 2

GXSTART = 100
GYSTART = 80
GWIDTH = WIDTH - GXSTART
GHEIGHT = HEIGHT - GYSTART
plot = displayio.Bitmap(GWIDTH, GHEIGHT, 4)

display_group.append(
    displayio.TileGrid(plot, pixel_shader=palette, x=GXSTART, y=GYSTART)
)

# Touchscreen setup
# ------Rotate 180:
screen_width = 320
screen_height = 240
ts = adafruit_touchscreen.Touchscreen(
    board.TOUCH_XR, board.TOUCH_XL,
    board.TOUCH_YU, board.TOUCH_YD,
    calibration=((5200, 59000), (5800, 57000)),
    size=(WIDTH, HEIGHT)
    )

class BBEcent(object):
    states = ("wait", "preheat", "ready", "recording", "reset")

    def __init__(self):
        with open("/config.json", mode="r") as fpr:
            self.config = json.load(fpr)
            fpr.close()
        with open("/profiles/" + self.config["profile"] + ".json", mode="r") as fpr:
            self.sprofile = json.load(fpr)
        self.set_state("ready")
    
    def set_profile(self, filename):
        with open("/profiles/" + filename + ".json", mode="r") as fpr:
            self.sprofile = json.load(fpr)
        

    def set_state(self, state):
        self.state = state
        self.check_state()
        self.last_state = state

    def check_state(self):
        if self.state == "wait":
            print("waiting")
        if self.state == "preheat":
            print("preheating")
        if self.state == "ready":
            print("ready")
        if self.state == "recording":
            print("recording")
        if self.state == "reset":
            print("reset")
            self.enable(True)

    def enable(self, enable):
        try:
            self.bbecent.value = enable
            self.control = enable
            if enable:
                print("BBEcent on")
            else:
                print("BBEcent off")
        except AttributeError:
            # bad sensor
            print("on/off function")
            pass



class Graph(object):
    def __init__(self):
        self.xmin = 0
        self.xmax = 50  # graph up to 50 seconds
        self.ymin = 0
        self.ymax = 100  #graph Pressure up to 10 bar x 10
        self.xstart = 1
        self.ystart = 5
        self.width = GWIDTH
        self.height = GHEIGHT

    # pylint: disable=too-many-branches
    def draw_line(self, x1, y1, x2, y2, size=PROFILE_SIZE, color=1, style=1):
        # print("draw_line:", x1, y1, x2, y2)
        # convert graph coords to screen coords
        x1p = self.xstart + self.width * (x1 - self.xmin) // (self.xmax - self.xmin)
        y1p = self.ystart + int(
            self.height * (y1 - self.ymin) / (self.ymax - self.ymin)
        )
        x2p = self.xstart + self.width * (x2 - self.xmin) // (self.xmax - self.xmin)
        y2p = self.ystart + int(
            self.height * (y2 - self.ymin) / (self.ymax - self.ymin)
        )
        # print("screen coords:", x1p, y1p, x2p, y2p)

        if (max(x1p, x2p) - min(x1p, x2p)) > (max(y1p, y2p) - min(y1p, y2p)):
            for xx in range(min(x1p, x2p), max(x1p, x2p)):
                if x2p != x1p:
                    yy = y1p + (y2p - y1p) * (xx - x1p) // (x2p - x1p)
                    if style == 2:
                        if xx % 2 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 3:
                        if xx % 8 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 4:
                        if xx % 12 == 0:
                            self.draw_point(xx, yy, size, color)
                    else:
                        self.draw_point(xx, yy, size, color)
        else:
            for yy in range(min(y1p, y2p), max(y1p, y2p)):
                if y2p != y1p:
                    xx = x1p + (x2p - x1p) * (yy - y1p) // (y2p - y1p)
                    if style == 2:
                        if yy % 2 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 3:
                        if yy % 8 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 4:
                        if yy % 12 == 0:
                            self.draw_point(xx, yy, size, color)
                    else:
                        self.draw_point(xx, yy, size, color)

    def draw_graph_point(self, x, y, size=PROFILE_SIZE, color=1):
        """ draw point using graph coordinates """

        # wrap around graph point when x goes out of bounds
        x = (x - self.xmin) % (self.xmax - self.xmin) + self.xmin
        xx = self.xstart + self.width * (x - self.xmin) // (self.xmax - self.xmin)
        yy = self.ystart + int(self.height * (y - self.ymin) / (self.ymax - self.ymin))
        print("graph point:", x, y, xx, yy)
        self.draw_point(xx, max(0 + size, yy), size, color)

    def draw_point(self, x, y, size=PROFILE_SIZE, color=1):
        """Draw data point on to the plot bitmap at (x,y)."""
        if y is None:
            return
        offset = size // 2
        for xx in range(x - offset, x + offset + 1):
            if xx in range(self.xstart, self.xstart + self.width):
                for yy in range(y - offset, y + offset + 1):
                    if yy in range(self.ystart, self.ystart + self.height):
                        try:
                            yy = GHEIGHT - yy
                            plot[xx, yy] = color
                        except IndexError:
                            pass


def draw_profile(graph, profile):
    """Update the display with current info."""
    for i in range(GWIDTH * GHEIGHT):
        plot[i] = 0

    # draw stage lines
    # preinfusion
    graph.draw_line(
        profile["stages"]["preinfusion"][0],
        (profile["P_range"][0]) * 10,
        profile["stages"]["preinfusion"][0],
        (profile["P_range"][1] + 6) * 10 ,
        GRID_SIZE,
        GRID_COLOR,
        GRID_STYLE,
    )
    graph.draw_line(
        profile["time_range"][0],
        (profile["stages"]["preinfusion"][1]) * 10,
        profile["time_range"][1],
        (profile["stages"]["preinfusion"][1])* 10,
        GRID_SIZE,
        GRID_COLOR,
        GRID_STYLE,
    )
    # peak
    graph.draw_line(
        profile["stages"]["peak"][0],
        profile["P_range"][0]* 10,
        profile["stages"]["peak"][0],
        profile["P_range"][1] * 60,
        GRID_SIZE,
        GRID_COLOR,
        GRID_STYLE,
    )
    graph.draw_line(
        profile["time_range"][0],
        profile["stages"]["peak"][1]* 10,
        profile["time_range"][1],
        profile["stages"]["peak"][1]* 10,
        GRID_SIZE,
        GRID_COLOR,
        GRID_STYLE,
    )
    # taper
    graph.draw_line(
        profile["stages"]["taper"][0],
        profile["P_range"][0]* 10,
        profile["stages"]["taper"][0]* 10,
        profile["P_range"][1] * 60,
        GRID_SIZE,
        GRID_COLOR,
        GRID_STYLE,
    )
    graph.draw_line(
        profile["time_range"][0],
        profile["stages"]["taper"][1]* 10,
        profile["time_range"][1],
        profile["stages"]["taper"][1]* 10,
        GRID_SIZE,
        GRID_COLOR,
        GRID_STYLE,
    )


    # draw labels
    x = profile["time_range"][0]
    y = profile["stages"]["taper"][1]
    xp = int(GXSTART + graph.width * (x - graph.xmin) // (graph.xmax - graph.xmin))
    yp = int(GHEIGHT * (y - graph.ymin) // (graph.ymax - graph.ymin))


    # draw time line (horizontal)
    graph.draw_line(
        graph.xmin,
        graph.ymin,
        graph.xmax, 
        graph.ymin, 
        AXIS_SIZE, 
        AXIS_COLOR, 1
    )
    graph.draw_line(
        graph.xmin, 
        graph.ymax, 
        graph.xmax - AXIS_SIZE, 
        graph.ymax, 
        AXIS_SIZE, 
        AXIS_COLOR, 1
    )
    # draw time ticks
    tick = graph.xmin
    while tick < ((graph.xmax - AXIS_SIZE)- graph.xmin + AXIS_SIZE) * 1.1:
        graph.draw_line(
            tick, graph.ymin, tick, graph.ymin + AXIS_SIZE, AXIS_SIZE, AXIS_COLOR, 1
        )
        graph.draw_line(
            tick,
            graph.ymax,
            tick,
            graph.ymax - AXIS_SIZE,
            AXIS_SIZE,
            AXIS_COLOR,
            1,
        )
        tick += 10

    # draw pressure line (vertical)
    graph.draw_line(
        graph.xmin,
        graph.ymin,
        graph.xmin,
        graph.ymax,
        AXIS_SIZE,
        AXIS_COLOR,
        1
    )
    graph.draw_line(
        graph.xmax - AXIS_SIZE,
        graph.ymin - AXIS_SIZE,
        graph.xmax - AXIS_SIZE,
        graph.ymax + AXIS_SIZE,
        AXIS_SIZE,
        AXIS_COLOR,
        1,
    )
  
    # draw pressure ticks
    tick = graph.ymin
    while tick < (graph.ymax - graph.ymin) * 10.1:
        graph.draw_line(
            graph.xmin + AXIS_SIZE,
            tick,
            graph.xmin, 
            tick, 
            AXIS_SIZE, 
            AXIS_COLOR, 
            1
        )
        graph.draw_line(
            graph.xmax - AXIS_SIZE,
            tick,
            graph.xmax - AXIS_SIZE - 1,
            tick,
            AXIS_SIZE,
            AXIS_COLOR,
            1,
        )
        tick += 10

    # draw profile
    x1 = profile["profile"][0][0]
    y1 = profile["profile"][0][1] * 10
    for point in profile["profile"]:
        x2 = point[0]
        y2 = point[1] * 10
        graph.draw_line(x1, y1, x2, y2, PROFILE_SIZE, PROFILE_COLOR, 1)
        # print(point)
        x1 = x2
        y1 = y2


def format_time(sec):
   sec = float(sec)
   min = int(sec) // 60
   sec %= 60
   return "%02d:%02d" % (min, sec) 


def isFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def is_Int(num):
    if isinstance(num,int):
        return True
    if isinstance(num,float):
        return num.is_integer()
    return False
    
def layerVisibility(state, layer, target):
    try:
        if state == "show":
            time.sleep(0.1)
            layer.append(target)
        elif state == "hide":
            layer.remove(target)
    except ValueError:
        pass
    
def switch_view(what_view):
    if what_view == 1:
        layerVisibility("show", display_group, view1)
    else:
        layerVisibility("hide", display_group, view1)
        




timediff = 0

font1 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")

font2 = bitmap_font.load_font("/fonts/OpenSans-12.bdf")

font3 = bitmap_font.load_font("/fonts/OpenSans-16.bdf")

bbecent = BBEcent()


#### Labels and Data Display ####


# Main Title #
title_label = label.Label(font3, text=TITLE)
title_label.x = 5
title_label.y = 14
display_group.append(title_label)
version_label = label.Label(font1, text=VERSION, color=0xAAAAAA)
version_label.x = 300
version_label.y = 5
display_group.append(version_label)

# Status Message#
screen_message = label.Label(font2, text="Wait", color=0xFFFFF0)
screen_message.x = 100
screen_message.y = 14
display_group.append(screen_message)

# Preheated Status
label_warm = label.Label(font1, text="Preheating", color=0xFF0000)
label_warm.x = 70
label_warm.y = 40
display_group.append(label_warm)

# Temp
temp_label = label.Label(font1, text="Temp(°C):", color=0xAAAAAA)
temp_label.x = 5
temp_label.y = 40
display_group.append(temp_label)
temp_data = label.Label(font1, text="Temperature")
temp_data.x = 10
temp_data.y = 60
display_group.append(temp_data)

#Pressure
pressure_label = label.Label(font1, text="Pressure:", color=0xAAAAAA)
pressure_label.x = 5
pressure_label.y = 80
display_group.append(pressure_label)
pressure_data = label.Label(font1, text="--")
pressure_data.x = 10
pressure_data.y = 100
display_group.append(pressure_data)

#Flow
flow_label = label.Label(font1, text="Flow:", color=0xAAAAAA)
flow_label.x = 5
flow_label.y = 120
display_group.append(flow_label)
flow_data = label.Label(font1, text="0 ml/s")
flow_data.x = 10
flow_data.y = 140
display_group.append(flow_data)

#Timer
timer_label = label.Label(font1, text="Time:", color=0xAAAAAA)
timer_label.x = 5
timer_label.y = 160
display_group.append(timer_label)
timer_data = label.Label(font3, text=format_time(timediff))
timer_data.x = 10
timer_data.y = 180
display_group.append(timer_data)

# Recording Circle Graphic
circle = Circle(190, 45, 8, fill=0)
display_group.append(circle)

# Clear Graph
square = Rect(100, 80, GWIDTH, GHEIGHT, fill=0)

# Graphing
sgraph = Graph()
# sgraph.xstart = 100
# sgraph.ystart = 4
sgraph.xstart = 0
sgraph.ystart = 0
# sgraph.width = WIDTH - sgraph.xstart - 4  # 216 for standard PyPortal
# sgraph.height = HEIGHT - 80  # 160 for standard PyPortal
sgraph.width = GWIDTH  # 216 for standard PyPortal
sgraph.height = GHEIGHT  # 160 for standard PyPortal
sgraph.xmin = bbecent.sprofile["time_range"][0]
sgraph.xmax = bbecent.sprofile["time_range"][1]
sgraph.ymin = bbecent.sprofile["P_range"][0] * 10
sgraph.ymax = bbecent.sprofile["P_range"][1] * 10.1
print("x range:", sgraph.xmin, sgraph.xmax)
print("y range:", sgraph.ymin, sgraph.ymax)
draw_profile(sgraph, bbecent.sprofile)


view1 = displayio.Group()  # Group for Profile buttons

# Button
buttons = []
button = Button(
    x=0, y=HEIGHT - 40, width=90, height=40, label="Start", label_font=font2
    )
buttons.append(button)

profile_button = Button(
    x=220, y=30, width=90, height=30, label="Profiles", label_font=font2
    )
buttons.append(profile_button)

for b in buttons:
    display_group.append(b)

profile1 = Button(
    x=110, y=90, width=90, height=40, label="Standard", label_font=font2
    )
view1.append(profile1)
profile2 = Button(
    x=210, y=90, width=90, height=40, label="Lever", label_font=font2
    )
view1.append(profile2)
profile3 = Button(
    x=110, y=140, width=90, height=40, label="Turbo", label_font=font2
    )
view1.append(profile3)

layerVisibility("hide", display_group, view1)
what_view = 1



#try:
 #   board.DISPLAY.refresh(target_frames_per_second=60)
#except AttributeError:
#    board.DISPLAY.refresh_soon()

# Display complete notification
print("display complete")

# Define various objects
last_temp = 0
last_state = "wait"
last_control = False
shot_time = 0.0
circle.fill = 0x0
second_timer = time.monotonic()
timer = 0
time_stamp = "00:00"
vol = 0.0
flow = 0.0
P = 0.0
#temp1 = 0
temp2 = 0.0
temp3 = 0.0
x1 = 0
yp1 = 0
yf1 = 0



while True:
    byte_read = uart.read(1)  # Read bytes over UART lines
    if byte_read is None:
        # Nothing read.
        continue
    if byte_read == b"<":
        # Start of message. Start accumulating bytes, but don't record the "<".
        message = []
        message_started = True
        continue
    if message_started:
        if byte_read == b">":
            message_parts = "".join(message).split(",")
            message_started = False
            valid = True
            if len(message_parts) != 6:
                # print("invalid message - Wrong length: {}".format(message_parts))
                valid = False
            else:
                for part in message_parts:
                    if not isFloat(part) or part == "" or is_Int(part):
                        # print("invalid message - invalid data: {}".format(message_parts))
                        valid = False
                        break
                   
            if valid:
                time_stamp, vol, flow, P, temp2, temp3 = message_parts
                temp_data.text = "Grp:{} Out:{}".format(temp2,temp3)
                flow_data.text ='{}ml/s'.format(flow)
                pressure_data.text= '{}bar'.format(P)
                # print(message_parts)
                if float(temp2) + float(temp3) <= 150.0 and bbecent.state != "preheat":
                    bbecent.set_state("preheat")
                elif bbecent.state == "recording":
                    #Start timing the shot
                    timediff = time.monotonic() - timer
                    timer_data.text = format_time(timediff)
                    shot_time = format_time(timediff)
                    #Graph using MuEditor
                    print((float(P),(float(flow))))
                    graph_P = float(P) * 10
                    graph_flow = float(flow) * 10
                    sgraph.draw_line(x1,yp1,int(timediff),int(graph_P), size=2, color=1, style=1)
                    sgraph.draw_line(x1,yf1,int(timediff),int(graph_flow), size=1, color=2, style=1)
                    
                    x1 = int(timediff)
                    yp1 = int(graph_P)
                    yf1 = int(graph_flow)
                    #Record to SD Card
                    try:
                        with open("/sd/log.txt", "a") as sdcard:
                            sdcard.write("{}, {}, {}, {}, {}\n".format(
                                time_stamp, temp2,
                                temp3, P, flow )
                                 )
                        #time.sleep(0.25)
                    except OSError:
                        print("OSError")
                        pass
                    except RuntimeError:
                        print("RuntimeError")
                        pass
                        print('not recording')
                #elif bbecent.state == "wait":
                    #screen_message.text == 'Status: Wait'
                    #label_warm.text = 'Preheating'
                elif bbecent.state == "preheat":
                    if float(temp2) + float(temp3) >= 150.0:
                        bbecent.set_state("ready")
                    else:
                        screen_message.text = 'Status: Preheating'
                elif bbecent.state == "reset":
                    label_warm.text = ''
                    print("Resetting Screen")
                    draw_profile(sgraph, bbecent.sprofile)
                    bbecent.set_state("ready")
                elif bbecent.state == "ready":
                    timer_data.text = format_time(time_stamp)
                    timer = time.monotonic()
                    screen_message.text = 'Status: Warmed & Ready'
                    label_warm.text = ''
                        
                    



        else:
            message.append(chr(byte_read[0]))






    touch = ts.touch_point
    if touch:
        print("touch!", touch[0],touch[1])
        if touch[0] >= 0 and touch[0] <= 80 and touch[1] >= 240 - 40 and touch[1] <= 240:
            if bbecent.state == "ready":
                button.label = "Recording"
                button.fill_color = 0xFF0000
                circle.fill = 0xFF0000
                screen_message.text = 'Status: Recording'
                bbecent.set_state("recording")
            elif bbecent.state == "recording":
                button.label = "Reset"
                button.fill_color = 0xFFFFFF
                circle.fill = 0x000000
                screen_message.text = 'Press Reset to Clear'
                bbecent.set_state("wait")
            elif bbecent.state == "wait":
                button.label = "Start"
                button.fill_color = 0xFFFFFF
                bbecent.set_state("reset")
            print("touch!", touch[0],touch[1])

            while ts.touch_point:
                pass
        # Profile Buttons
        if touch[0] >= 200 and touch[0] <= 320 and touch[1] >= 20 and touch[1] <= 70:
            switch_view(what_view)
            if what_view == 1:
                what_view = 2
            else:
                what_view = 1
            print("touch!", touch[0],touch[1])
            print("Show Profiles")
            while ts.touch_point:
                pass
        #profile_button
        if touch[0] >= 110 and touch[0] <= 200 and touch[1] >= 90 and touch[1] <= 130:
            print("touch!", touch[0],touch[1])
            print("Standard")
            switch_view(2)
            bbecent.set_profile("standard")
            draw_profile(sgraph, bbecent.sprofile)
            while ts.touch_point:
                pass
        if touch[0] >= 210 and touch[0] <= 300 and touch[1] >= 90 and touch[1] <= 130:
            print("touch!", touch[0],touch[1])
            print("Lever")
            switch_view(2)
            bbecent.set_profile("lever")
            draw_profile(sgraph, bbecent.sprofile)
            while ts.touch_point:
                pass
        if touch[0] >= 110 and touch[0] <= 200 and touch[1] >= 140 and touch[1] <= 180:
            print("Turbo")
            switch_view(2)
            bbecent.set_profile("turbo")
            draw_profile(sgraph, bbecent.sprofile)
            while ts.touch_point:
                pass
        time.sleep(0.2)  # for debounce


# 3 humidifier controller

import machine
import sys
import time
from dht20 import DHT20
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY
from pimoroni import RGBLED


########################
# Constants
#
VERSION = "1.0.1"


# Overall settings
#
BAR_DISPLAY_SECS = 5      # How often to refresh the bar display screen
RH_UPDATE_SECS   = 300    # How often to read the sensor to update relative humidity (RH)
TICK_INTERVAL    = 24     # How often to draw ticks (longer bars) on RH plot.  Interval of 24 ticks with 300 second updates means a tick every two hours of data
AUTOMATE_SECS    = 5      # How often to check whether the automation settings (relays) need updating
HEARTBEAT_MS     = 1000   # How often to blink the heartbeat circle in the upper left corner

DEFAULT_ON_RH    = 66.0   # Turn on one low humidifier if RH drops below the ON threshold (default setting)
DEFAULT_LOW_RH   = 55.0   # Turn on all humidifiers if RH drops below the LOW threshold (default setting)

WARN_PCT         = 30.0   # When a humidifier is this % or less full, show its bar yellow.  If on low and one is available, switch to another lo humidifier
ERROR_PCT        = 10.0   # When a humidifier is this % or less full, show its bar red.


# Set to fake RH
FAKE_RH = True
if FAKE_RH:
    RH_UPDATE_SECS = 7
    

# Main bar screen settings
#
HI_X_MIN = [   7,  84, 161 ]                     # coordinates of the humidifier bars
HI_X_MAX = [  79, 156, 233 ]                     # coordinates of the humidifier bars
LO_X_MIN = [  31, 108, 185 ]                     # coordinates of the humidifier bars
LO_X_MAX = [  55, 132, 209 ]                     # coordinates of the humidifier bars

LIGHTNING_POLYGON = [ [  4,  0 ],                # polygon making lightning bolt
                      [ 10,  0 ],                # ... continued ...
                      [  6,  6 ],                # ... continued ...
                      [  9,  6 ],                # ... continued ...
                      [  0, 20 ],                # ... continued ...
                      [  4, 10 ],                # ... continued ...
                      [  1, 10 ] ]               # ... end of polygon
LIGHTNING_POLYGON_HEIGHT = 20                    # lightning bolt height in pixels

HEARTBEAT_CIRCLE_SIZE = 5                        # diameter for heartbeat circle
HEARTBEAT_X = int(HEARTBEAT_CIRCLE_SIZE / 2) + 1 # X coordinate of center of heartbeat circle
HEARTBEAT_Y = int(HEARTBEAT_CIRCLE_SIZE / 2) + 1 # Y coordinate of center of heartbeat circle

MIN_RH_PLOT_PCT = 45                             # Min RH of background line graph behind displayed RH value
MAX_RH_PLOT_PCT = 75                             # Max RH of background line graph behind displayed RH value
RH_SCALE        = 1.5                            # Scaling factor for text displaying RH value

HI_PCT_USED_PER_SECOND = 100.0 / (11 * 60 * 60 + 45 * 60)  # Number of seconds a humidifier at HI should last (11h, 45m)
LO_PCT_USED_PER_SECOND = 100.0 / (23 * 60 * 60 + 30 * 60)  # Number of seconds a humidifier at HI should last (23h, 30m)

UP_ARROW_LINES =   [ [ 5,  0,  8,  0 ],          # Line description for RH trending UP line
                     [ 8,  0,  9,  3 ],          # Line description for RH trending UP line
                     [ 8,  0,  0, 20 ] ]         # Line description for RH trending UP line
DOWN_ARROW_LINES = [ [ 5, 20,  8, 20 ],          # Line description for RH trending DOWN line
                     [ 8, 20,  9, 17 ],          # Line description for RH trending DOWN line
                     [ 8, 20,  0,  0 ] ]         # Line description for RH trending DOWN line
EVEN_ARROW_LINES = [ [ 5,  7,  8, 10 ],          # Line description for RH trending EVEN line
                     [ 5, 13,  8, 10 ],          # Line description for RH trending EVEN line
                     [ 0, 10,  8, 10 ] ]         # Line description for RH trending EVEN line
ARROW_HEIGHT = 20                                # Height of RH trend arrow

RH_READINGS_TO_TREND = 5                         # How many RH readings to average for trending



# For Menu screens settings
#
MENU_ENTRY_RECTS = [ { "x_min" : 30, "x_max" : 210, "y_min" :  4, "y_max":  44 },  # Coordinates of the menu entry text fields
                     { "x_min" : 30, "x_max" : 210, "y_min" : 48, "y_max":  88 },  # Coordinates of the menu entry text fields
                     { "x_min" : 30, "x_max" : 210, "y_min" : 92, "y_max": 132 } ] # Coordinates of the menu entry text fields

MENU_TEXT_SCALE = 0.75                     # Scale factor for menu text
NUMBER_SCALE    = 2.0                      # Scale factor for showing number in menu (when setting RH thresholds)
VERSION_SCALE   = 1.5                      # Scale factor for showing version in menu

HUMIDIFIER_MENU = [ { "text" : "OFF",  "action" : "humidifier_off" },           # Humidifier setting sub-menu entries
                    { "text" : "LO",   "action" : "humidifier_lo" },            #   ...
                    { "text" : "HI",   "action" : "humidifier_hi" } ]           #   ...

SETTINGS_MENU = [ { "text": "ON RH%",  "action" : "show_settings_menu_on" },    # Humidifier settings sub-menu entries
                  { "text": "LOW RH%", "action" : "show_settings_menu_low" } ]  #   ...

TOP_MENU = [ { "text" : "Humidifier 1", "action" : "show_humidifier_menu_1" },  # Top level menu entries
             { "text" : "Humidifier 2", "action" : "show_humidifier_menu_2" },  #   ...
             { "text" : "Humidifier 3", "action" : "show_humidifier_menu_3" },  #   ...
             { "text" : "Refill",       "action" : "humidifiers_refilled" },    #   ...
             { "text" : "RH Settings",  "action" : "show_settings_menu" },      #   ...
             { "text" : "Version",      "action" : "show_version" } ]           #   ...

MENU_IDLE_SECS_EXIT = 5          # Seconds of no button press at which to automatically exit menu screens
DEBOUNCE_MS         = 150        # min ms between button presses to debounce switch noise


DEBOUNCE_RH_AMOUNT = 0.5         # Debounce RH settings.  When crossing a RH threshold, must pass it by this much before considered crossing
RH_SAMPLES_PER_READ = 5          # Read the sensor this many times and average for each RH reading



# Pico settings
#
OUTLET_PIN_NUMBERS = [ 3, 4, 5 ]     # GPIO pins of the outlet (relay) controls
SDA_PIN_NUMBER = 0                   # GPIO pin for sensor SDA (data)
SCL_PIN_NUMBER = 1                   # GPIO pin for sensor SCL (clock)
HMIDITY_SENSOR_POWER_PIN_NUMBER = 2  # GPIO pin for sensor power
HUMIDITY_SENSOR_ADDRESS = 0x38       # I2C address of sensor

#
########################


on_rh  = DEFAULT_ON_RH     # on_rh holds the currently set "ON" RH threshold where light humidifying happens
low_rh = DEFAULT_LOW_RH    # low_rh holds the currently set "LOW" RH threshold where heavy humidifying happens
current_rh = 0.0           # The current RH returned from the sensor
rh_trend = 0               # The RH trend.  Either -1 (falling), 0 (even) or 1 (rising)
humidifying = "off"        # current humidifying activity - "off" or "light" or "heavy"

should_refresh_display = False   # When set, causes the display to be refreshed immediately instead of at next update interval


# Represents each of the 3 humidifiers (outlets)
#   setting             The setting of the humidifier plugged into this outlet - "hi", "lo" or "off" (off means off or not one plugged in)
#   energized           Whether this humidifier's outlet is currently energized
#   filled_time         Time when this humidifier was last filled
#   last_setting_time   Time when this humidifier's setting was last changed (e.g. between "off" "lo" and "hi")
#   lo_secs             Number of seconds this humidifier has been run on "lo" since being filled - does not count run time from last_setting_time
#   hi_secs             Number of seconds this humidifier has been run on "hi" since being filled - does not count run time from last_setting_time
#   outlet              The outlet number for this humidifier (also its index in this array)
humidifiers = [ { "setting" : "lo",
                  "energized" : False,
                  "filled_time" : 0,
                  "last_setting_time" : time.time(),
                  "lo_secs" : 0,
                  "hi_secs" : 0,
                  "outlet" : 0 },
                { "setting" : "lo",
                  "energized" : False,
                  "filled_time" : 0,
                  "last_setting_time" : time.time(),
                  "lo_secs" : 0,
                  "hi_secs" : 0,
                  "outlet" : 1 },
                { "setting" : "hi",
                  "energized" : False,
                  "filled_time" : 0,
                  "last_setting_time" : time.time(),
                  "lo_secs" : 0,
                  "hi_secs" : 0,
                  "outlet" : 2 } ]

last_button_press_secs = 0          # time of the last button press - used for menu idle timeout
last_button_ms = time.ticks_ms()    # ms resolution time of last button press - used for de-bouncing buttons
heartbeat_on = False                # indicator of whether the heartbeat circle is currently shown or not - gets toggled at heartbeat interval


######## FAKE RH ###############################
fake_rh_ascending = True  # Is fake RH ascending (or descending)
fake_rh_step = 0.7        # How much to step fake RH at each reading
fake_rh_hi = 72.0         # When fake RH is above this, start descending fake RH
fake_rh_low = 48.0        # When fake RH is below this, start ascending fake RH
######## FAKE RH ###############################



#######################################################
################# BEGIN LOGGER ########################
#######################################################
#
def log_message(message):
    year, month, day, hour, minute, second, micro, milli = time.localtime()

    print("%02d:%02d:%02d %s" % (hour, minute, second, message))
#######################################################
################## END LOGGER #########################
#######################################################
    




#######################################################
############## BEGIN DISPLAY SETUP ####################
#######################################################
#
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=0)
WIDTH, HEIGHT = display.get_bounds()
HALF_HEIGHT = int(HEIGHT/2)
HALF_WIDTH = int(WIDTH/2)

# List of available pen colours, add more if necessary
RED     = display.create_pen(209,  34,  41)
ORANGE  = display.create_pen(246, 138,  30)
YELLOW  = display.create_pen(255, 216,   0)
GREEN   = display.create_pen(  0, 121,  64)
INDIGO  = display.create_pen( 36,  64, 142)
VIOLET  = display.create_pen(115,  41, 130)
WHITE   = display.create_pen(255, 255, 255)
PINK    = display.create_pen(255, 175, 200)
BLUE    = display.create_pen(116, 215, 238)
BROWN   = display.create_pen( 97,  57,  21)
BLACK   = display.create_pen(  0,   0,   0)
MAGENTA = display.create_pen(255,  33, 140)
CYAN    = display.create_pen( 33, 177, 255)
GRAY    = display.create_pen( 24,  24,  24)

LED = RGBLED(6, 7, 8) # pins 6, 7, 8
LED.set_rgb(0, 0, 0)
#######################################################
############### END DISPLAY SETUP #####################
#######################################################


# Keep one historical RH reading for each pixel of display width
MAX_PREV_RH_READINGS = WIDTH
prev_rh_readings = [ 0 ] * MAX_PREV_RH_READINGS


# setup outlet control pins
outlet_Pins = []
for i in range(len(OUTLET_PIN_NUMBERS)):
    outlet_Pins.append(machine.Pin(OUTLET_PIN_NUMBERS[i], machine.Pin.OUT))
    outlet_Pins[i].value(0)


# setup I2C pins for reading humidity sensor
log_message("Setting up I2C...")
sda = machine.Pin(SDA_PIN_NUMBER)
scl = machine.Pin(SCL_PIN_NUMBER)
i2c = machine.I2C(0, sda=sda, scl=scl, freq=400000)
sensor_power_pin = machine.Pin(HMIDITY_SENSOR_POWER_PIN_NUMBER, machine.Pin.OUT)



#######################################################
########### BEGIN ERROR TEXT DISPLAY ##################
#######################################################
#
# Display the error text on the display
#
def display_error_text(error_text):
    log_message("ERROR TEXT: " + error_text)
    display.set_pen(RED)
    display.set_font("bitmap6")
    display.text(error_text, 0, 0, wordwrap=HEIGHT)
    display.update()
#######################################################
############ END ERROR TEXT DISPLAY ##################$
#######################################################



#######################################################
############### BEGIN LED CONTROL #####################
#######################################################
#
def clear_led():
    LED.set_rgb(0, 0, 0)

def led_red(bright=False):
    if bright:
        LED.set_rgb(128, 0, 0)
    else:
        LED.set_rgb(8, 0, 0)

def led_green(bright=False):
    if bright:
        LED.set_rgb(0, 128, 0)
    else:
        LED.set_rgb(0, 8, 0)
        
def led_rgb(r, g, b):
    LED.set_rgb(r, g, b)
#
#######################################################
################ END LED CONTROL ######################
#######################################################



#######################################################
########## BEGIN HUMIDIFIER BARS SCREEN ###############
#######################################################
#
# Calculate pct used for humidifier.
# This includes the lo_secs, hi_secs and the amount of time
# at "lo" or "hi" since the last_setting_time.
#
def calculate_pct_used(humidifier):
    # calculate total lo and hi secs used
    lo_secs = humidifier["lo_secs"]
    if humidifier["setting"] == "lo" and humidifier["energized"]:
        lo_secs = lo_secs + time.time() - humidifier["last_setting_time"]
    hi_secs = humidifier["hi_secs"]
    if humidifier["setting"] == "hi" and humidifier["energized"]:
        hi_secs = hi_secs + time.time() - humidifier["last_setting_time"]
    # calculate pct used from the secs
    pct_used = float(lo_secs) * LO_PCT_USED_PER_SECOND + float(hi_secs) * HI_PCT_USED_PER_SECOND
    #log_message("pct_used for humidifier %d : %.1f" % (humidifier["outlet"], pct_used))
    return pct_used


#
# Calculate the Y value for a RH value
#
def calculate_RH_y(rh, max_y):
    if rh == 0:
        return -1
    if rh > MAX_RH_PLOT_PCT:
        rh = MAX_RH_PLOT_PCT
    if rh < MIN_RH_PLOT_PCT:
        rh = MIN_RH_PLOT_PCT
    y = int(max_y - ((rh - MIN_RH_PLOT_PCT)/(MAX_RH_PLOT_PCT - MIN_RH_PLOT_PCT)) * max_y)
    return y


#
# Display the humidifier bars screen.  This includes:
#   RH history graph in background on top half
#   Current RH % in text format on top half.
#   RH trend arrow after the current RH on top half.
#   Capacity bar for each humidifier on bottom half.
#   Lightning bolt for each energized humidifier on bottom half.
#
def display_humidifier_bars():
    # clear the display
    display.set_pen(BLACK)
    display.clear()
    
    # show RH plot in background.
    # Include a "tick" (additional pixels) at every TICK_INTERVAL - which if set correctly should align with each hour back
    display.set_pen(INDIGO)
    since_tick = 0
    draw_tick = False
    for i in range(0, WIDTH):
        if since_tick >= TICK_INTERVAL:
            draw_tick = True
            since_tick = 0
        else:
            since_tick = since_tick + 1
        reading_index = WIDTH - i - 1
        if prev_rh_readings[reading_index] > 0:
            display.pixel(i, calculate_RH_y(prev_rh_readings[reading_index], HALF_HEIGHT - 10))
            if draw_tick:
                display.set_pen(YELLOW)
                display.pixel(i, 0)
                display.pixel(i, 1)
                display.pixel(i, calculate_RH_y(prev_rh_readings[reading_index], HALF_HEIGHT - 10)+2)
                display.pixel(i, calculate_RH_y(prev_rh_readings[reading_index], HALF_HEIGHT - 10)-2)
                display.pixel(i, HALF_HEIGHT - 10)
                display.pixel(i, HALF_HEIGHT - 11)
                display.set_pen(INDIGO)
                draw_tick = False

    # show the current RH as a number and percent sign
    rh_text = "%.1f%%" % current_rh
    display.set_pen(RED)
    display.set_font("sans")
    text_width = display.measure_text(rh_text, RH_SCALE)
    x_start = HALF_WIDTH - int(text_width/2)
    y_midline = int(HALF_HEIGHT/2)
    display.text(rh_text, x_start, y_midline, scale = RH_SCALE)
    
    # show the trend - up, even or down arrow
    arrow_x = x_start + text_width + 5
    arrow_y = y_midline - int(ARROW_HEIGHT/2)
    arrow_lines = []
    if rh_trend == 1:
        for i in range(len(UP_ARROW_LINES)):
            arrow_lines.append((UP_ARROW_LINES[i][0] + arrow_x, UP_ARROW_LINES[i][1] + arrow_y, UP_ARROW_LINES[i][2] + arrow_x, UP_ARROW_LINES[i][3] + arrow_y))
    elif rh_trend == -1:
        for i in range(len(DOWN_ARROW_LINES)):
            arrow_lines.append((DOWN_ARROW_LINES[i][0] + arrow_x, DOWN_ARROW_LINES[i][1] + arrow_y, DOWN_ARROW_LINES[i][2] + arrow_x, DOWN_ARROW_LINES[i][3] + arrow_y))
    else:
        for i in range(len(EVEN_ARROW_LINES)):
            arrow_lines.append((EVEN_ARROW_LINES[i][0] + arrow_x, EVEN_ARROW_LINES[i][1] + arrow_y, EVEN_ARROW_LINES[i][2] + arrow_x, EVEN_ARROW_LINES[i][3] + arrow_y))
    for line in arrow_lines:
        display.line(line[0], line[1], line[2], line[3])


    # Show the bars - wide bar for humidifier set to "hi", thin for "lo" and height based on pct remaining.
    # If the humidifier is currently energized, also show the lightning bolt
    pcts_available = []
    for i in range(len(humidifiers)):
        pct_used = calculate_pct_used(humidifiers[i])
        #log_message("humidifier %d: pct_used = %.3f" % ( i, pct_used))
        pct_available = 100.0 - pct_used
        pcts_available.append(pct_available)
        #log_message("humidifier %d: pct_available = %.3f" % ( i, pct_available))
        
        # calculate bar height (y_max)
        height = int(float(HALF_HEIGHT) * pct_available / 100.0)
        
        # determine x_min, x_max and pen color
        if humidifiers[i]["setting"] == "hi":
            x_min = HI_X_MIN[i]
            x_max = HI_X_MAX[i]
        elif humidifiers[i]["setting"] == "lo":
            x_min = LO_X_MIN[i]
            x_max = LO_X_MAX[i]
        else:
            x_min = HI_X_MIN[i]
            x_max = HI_X_MAX[i]
        if humidifiers[i]["setting"] == "off":
            pen = GRAY
        elif pct_available < ERROR_PCT:
            pen = RED
        elif pct_available < WARN_PCT:
            pen = YELLOW
        else:
            pen = GREEN
        
        # draw the rectangle
        display.set_pen(pen)
        display.rectangle(x_min, HEIGHT - height, x_max - x_min, height)
        
        # if energized, draw the blue lightning
        if humidifiers[i]["energized"]:
            display.set_pen(BLUE)
            lightning_x = x_min + int((x_max - x_min)/2)
            lightning_y = HALF_HEIGHT
            bar_poly = []
            for i in range(len(LIGHTNING_POLYGON)):
                bar_poly.append((LIGHTNING_POLYGON[i][0] + lightning_x, LIGHTNING_POLYGON[i][1] + lightning_y))
            display.polygon(bar_poly)

    log_message("humidifier %d: %.3f%%,  %d: %.3f%%,  %d: %.3f%%" % ( 0, pcts_available[0], 1, pcts_available[1], 2, pcts_available[2]))

    display.update()
#
#######################################################
########### END HUMIDIFIER BARS SCREEN ################
#######################################################


#######################################################
############## BEGIN ACTIONS ##########################
#######################################################
#
# Update relay settings for each humidifier based on whether its outlet is energized
# Turn on or off the outlet's GPIO pin to control the outlet's relay
#
def update_relays():
    global outlet_Pins
    global should_refresh_display
    for i in range(len(humidifiers)):
        if humidifiers[i]["energized"]:
            if outlet_Pins[i].value() == 0:
                log_message("Energizing relay %d" % i)
                outlet_Pins[i].value(1)
                should_refresh_display = True
        else:
            if outlet_Pins[i].value() == 1:
                log_message("De-energizing relay %d" % i)
                outlet_Pins[i].value(0)
                should_refresh_display = True


#
# update humidifier usage - if switching setting from "lo" or "hi", update lo_secs or hi_secs to include the number of seconds
# it as run at that setting since the last_setting_time.  Reset the humidifier's last_setting_time.
# This should be called prior to changing the humidifier setting.
#
def update_humidifier_usage(humidifier):
    log_message("Updating usage for humidifier %d" % humidifier["outlet"])
    if humidifier["energized"] and humidifier["setting"] == "lo":
        humidifier["lo_secs"] = humidifier["lo_secs"] + time.time() - humidifier["last_setting_time"]
        humidifier["last_setting_time"] = time.time()
    elif humidifier["energized"] and humidifier["setting"] == "hi":
        humidifier["hi_secs"] = humidifier["hi_secs"] + time.time() - humidifier["last_setting_time"]
        humidifier["last_setting_time"] = time.time()


#
# de-energize the humidifier
# Update this humidifier's usage and set it as not energized
#
def deenergize_humidifier(humidifier):
    log_message("De-energizing humidifier %d" % humidifier["outlet"])
    update_humidifier_usage(humidifier)
    humidifier["energized"] = False
    update_relays()


#
# energize the humidifier
# Update this humidifier's usage and set it as energized
#
def energize_humidifier(humidifier):
    log_message("Energizing humidifier %d" % humidifier["outlet"])
    update_humidifier_usage(humidifier)
    humidifier["energized"] = True
    update_relays()


#
# Calculate needed humidifying setting.  Will return "off", "light" or "heavy"
#
def determine_needed_humidifying():
    if humidifying == "off":
        if current_rh > (on_rh - DEBOUNCE_RH_AMOUNT):
            needed_humidifying = "off"
        elif current_rh > (low_rh - DEBOUNCE_RH_AMOUNT):
            needed_humidifying = "light"
        else:
            needed_humidifying = "heavy"
    elif humidifying == "light":
        if current_rh > (on_rh + DEBOUNCE_RH_AMOUNT):
            needed_humidifying = "off"
        elif current_rh < (low_rh - DEBOUNCE_RH_AMOUNT):
            needed_humidifying = "heavy"
        else:
            needed_humidifying = "light"
    else: # heavy
        if current_rh > (on_rh + DEBOUNCE_RH_AMOUNT):
            needed_humidifying = "off"
        elif current_rh > (low_rh + DEBOUNCE_RH_AMOUNT):
            needed_humidifying = "light"
        else:
            needed_humidifying = "heavy"
    if needed_humidifying != humidifying:
        log_message("determine_needed_humidifying determined %s" % needed_humidifying)
    return needed_humidifying


#
# Choose which humidifier to use for light humidifying
#
def choose_humidifiers_light():
    
    # see what humidifiers are currently energized
    energized_lo = []
    energized_hi = []
    all_lo = []
    all_hi = []
    for i in range(len(humidifiers)):
        pct_used = calculate_pct_used(humidifiers[i])
        if humidifiers[i]["setting"] == "lo":
            all_lo.append({ "outlet" : i, "pct_used" : pct_used})
        elif humidifiers[i]["setting"] == "hi":
            all_hi.append({ "outlet" : i, "pct_used" : pct_used})
        if humidifiers[i]["energized"]:
            if humidifiers[i]["setting"] == "lo":
                energized_lo.append({ "outlet" : i, "pct_used" : pct_used})
            elif humidifiers[i]["setting"] == "hi":
                energized_hi.append({ "outlet" : i, "pct_used" : pct_used})
    log_message("choose_humidifiers_light found energized humidifiers: %d lo, %d hi, total humidifiers %d lo, %d hi" % (len(energized_lo), len(energized_hi), len(all_lo), len(all_hi)))

    energized_lo = sorted(energized_lo, key=lambda d: d['pct_used'])
    energized_hi = sorted(energized_hi, key=lambda d: d['pct_used'])
    all_lo = sorted(all_lo, key=lambda d: d['pct_used'])
    all_hi = sorted(all_hi, key=lambda d: d['pct_used'])
    log_message("light energized_lo = %s" % str(energized_lo))
    log_message("light energized_hi = %s" % str(energized_hi))
    log_message("light all_lo = %s" % str(all_lo))
    log_message("light all_hi = %s" % str(all_hi))
    
    # if none are currently energized...
    if len(energized_lo) + len(energized_hi) == 0:
        
        # if any lo humidifiers, use the least used one if not error level
        if len(all_lo):
            if all_lo[0]["pct_used"] < (100.0 - ERROR_PCT):
                log_message("light energizing lo humidifier %d" % all_lo[0]["outlet"])
                energize_humidifier(humidifiers[all_lo[0]["outlet"]])
                return
        # no lo available, any hi
        if len(all_hi):
            if all_hi[0]["pct_used"] < (100 - ERROR_PCT):
                log_message("light energizing hi humidifier %d" % all_hi[0]["outlet"])
                energize_humidifier(humidifiers[all_hi[0]["outlet"]])
                return
        # no non-error humidifiers.  Energize any humidifiers
        if len(all_lo):
            log_message("light desparately energizing lo humidifier %d at %.3f pct used" % (all_lo[0]["outlet"], all_lo[0]["pct_used"]))
            energize_humidifier(humidifiers[all_lo[0]["outlet"]])
            return
        if len(all_hi):
            log_message("light desparately energizing hi humidifier %d at %.3f pct used" % (all_hi[0]["outlet"], all_hi[0]["pct_used"]))
            energize_humidifier(humidifiers[all_hi[0]["outlet"]])
            return
        
        # NO humidifier available - but need one!  Set the led
        led_red(bright=True)
        log_message("NO HUMIDIFIER AVAILALBE!!!")
        return
    
    # is one lo already on and healthy?
    if len(energized_lo) == 1 and len(energized_hi) == 0 and energized_lo[0]["pct_used"] < (100.0 - ERROR_PCT):
        log_message("light continuing to use lo humidifier %d" % energized_lo[0]["outlet"])
        return
    
    # choose from scratch!
    # de-energize all and we'll energize the one we want to use
    for i in range(len(humidifiers)):
        deenergize_humidifier(humidifiers[i])
    # is a lo non-erro available?
    if len(all_lo):
        if all_lo[0]["pct_used"] < (100.0 - ERROR_PCT):
            log_message("light energizing lo humidifier %d" % all_lo[0]["outlet"])
            energize_humidifier(humidifiers[all_lo[0]["outlet"]])
            return
    # no lo non-error available, any hi non-error?
    if len(all_hi):
        if all_hi[0]["pct_used"] < (100 - ERROR_PCT):
            log_message("light energizing hi humidifier %d" % all_hi[0]["outlet"])
            energize_humidifier(humidifiers[all_hi[0]["outlet"]])
            return
    # no non-error humidifiers.  Energize any humidifiers
    if len(all_lo):
        log_message("light desparately energizing lo humidifier %d at %.3f pct used" % (all_lo[0]["outlet"], all_lo[0]["pct_used"]))
        energize_humidifier(humidifiers[all_lo[0]["outlet"]])
        return
    if len(all_hi):
        log_message("light desparately energizing hi humidifier %d at %.3f pct used" % (all_hi[0]["outlet"], all_hi[0]["pct_used"]))
        energize_humidifier(humidifiers[all_hi[0]["outlet"]])
        return
        
    # NO humidifier available - but need one!  Set the led
    led_red(bright=True)
    log_message("NO HUMIDIFIER AVAILALBE!!!")


#
# For heavy, energize all humidifiers
#
def choose_humidifiers_heavy():
    
    for i in range(len(humidifiers)):
        if not humidifiers[i]["energized"]:
            if humidifiers[i]["setting"] != "off":
                energize_humidifier(humidifiers[i])


#
# Determine what to energize
#
def automate_energizing():
    global humidifying
    needed_humidifying = determine_needed_humidifying()
    
    if needed_humidifying == "off":
        if humidifying == "off":
            log_message("humidifying staying off, current_rh = %.1f%%, above %.1f%% (debounce=%.1f%%), staying off" % (current_rh, on_rh, DEBOUNCE_RH_AMOUNT))
        else:
            log_message("humidifying turning off, current_rh = %.1f%%, above %.1f%% (debounce=%.1f%%), staying off" % (current_rh, on_rh, DEBOUNCE_RH_AMOUNT))
            humidifying = "off"
            for i in range(len(humidifiers)):
                deenergize_humidifier(humidifiers[i])
    
    elif needed_humidifying == "light":
        choose_humidifiers_light()
        humidifying = "light"
    else:
        choose_humidifiers_heavy()
        humidifying = "heavy"
    


#
# Set a humidifier as refilled
#
def humidifier_refilled(humidifier):
    humidifier["filled_time"] = time.time()
    humidifier["last_setting_time"] = time.time()
    humidifier["lo_secs"] = 0
    humidifier["hi_secs"] = 0


#
# Set a humidifier setting
#
def humidifier_setting(humidifier, new_setting):
    secs = time.time() - humidifier["last_setting_time"]
    update_humidifier_usage(humidifier)
    humidifier["last_setting_time"] = time.time()
    humidifier["setting"] = new_setting
#
#######################################################
############### END ACTIONS ###########################
#######################################################


#######################################################
############### BEGIN MENU ###########################$
#######################################################
#
# Setup button handling
#
a_pressed = False
b_pressed = False
x_pressed = False
y_pressed = False

def button_a_handler(pin):
    global a_pressed
    global last_button_ms
    global DEBOUNCE_MS
    if time.ticks_diff(time.ticks_ms(), last_button_ms) < DEBOUNCE_MS:
        return
    last_button_ms = time.ticks_ms()
    a_pressed = True

def button_b_handler(pin):
    global b_pressed
    global last_button_ms
    global DEBOUNCE_MS
    if time.ticks_diff(time.ticks_ms(), last_button_ms) < DEBOUNCE_MS:
        return
    last_button_ms = time.ticks_ms()
    b_pressed = True

def button_x_handler(pin):
    global x_pressed
    global last_button_ms
    global DEBOUNCE_MS
    if time.ticks_diff(time.ticks_ms(), last_button_ms) < DEBOUNCE_MS:
        return
    last_button_ms = time.ticks_ms()
    x_pressed = True

def button_y_handler(pin):
    global y_pressed
    global last_button_ms
    global DEBOUNCE_MS
    if time.ticks_diff(time.ticks_ms(), last_button_ms) < DEBOUNCE_MS:
        return
    last_button_ms = time.ticks_ms()
    y_pressed = True

# ORIGINAL
#def button_y_handler(pin):
#    global y_pressed
#    if pin.value() == 0:
#        y_pressed = True

#
# defining buttons and their irq handlers
#
button_a = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
button_b = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
button_x = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
button_y = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
button_a.irq(trigger = machine.Pin.IRQ_FALLING, handler=button_a_handler)
button_b.irq(trigger = machine.Pin.IRQ_FALLING, handler=button_b_handler)
button_x.irq(trigger = machine.Pin.IRQ_FALLING, handler=button_x_handler)
button_y.irq(trigger = machine.Pin.IRQ_FALLING, handler=button_y_handler)


#
# Display a menu entry and the rectangle provide
#
def draw_menu_entry(entry, menu_entry_rect, is_selected):
    # set pen based on whether selected or not
    # { "x_min" : 30, "x_max" : 210, "y_min" :  4, "y_max":  44 }
    entry_width = menu_entry_rect["x_max"] - menu_entry_rect["x_min"]
    entry_height = menu_entry_rect["y_max"] - menu_entry_rect["y_min"]
    y_midline = round(menu_entry_rect["y_min"] + (entry_height / 2))
    display.set_clip(menu_entry_rect["x_min"],
                     menu_entry_rect["y_min"],
                     entry_width,
                     entry_height)
    #log_message("y_midline=%d, clip rect=%d, %d, %d, %d" % (y_midline, menu_entry_rect["x_min"], menu_entry_rect["y_min"], entry_width, entry_height))

    # if selected entry, set the background to green
    if is_selected:
        display.set_pen(GREEN)
        disp_w, disp_h = display.get_bounds()
        display.rectangle(0, 0, disp_w, disp_h)

    display.set_pen(RED)
    display.set_font("sans")
    text_width = display.measure_text(entry["text"], MENU_TEXT_SCALE)
    x_start = menu_entry_rect["x_max"] - text_width - 1
    display.text(entry["text"], x_start, y_midline, scale = MENU_TEXT_SCALE)
    display.remove_clip()
    

#
# Display a list of menu entries
#
def show_menu_entries(entries, menu_selection):
    # clear display
    display.set_pen(BLACK)
    display.clear()
    # wrap selection
    if menu_selection < 0:
        menu_selection = len(entries) - 1
    elif menu_selection >= len(entries):
        menu_selection = 0
    # do we need to start below the top?
    if menu_selection >= len(MENU_ENTRY_RECTS):
        top_entry = menu_selection - len(MENU_ENTRY_RECTS) + 1
    else:
        top_entry = 0
    
    # display each entry
    for i in range(len(MENU_ENTRY_RECTS)):
        if top_entry + i < len(entries):    
            draw_menu_entry(entries[top_entry + i], MENU_ENTRY_RECTS[i], menu_selection == top_entry + i)
    # update the display
    display.update()
    return menu_selection


#
# Display a menu entry and the rectangle provide
#
def show_setting(value):
    display.set_pen(BLACK)
    display.clear()
    
    display.set_pen(RED)
    display.set_font("sans")
    text_width = display.measure_text(str(value), NUMBER_SCALE)
    x_start = int( HALF_WIDTH - (text_width/2))
    display.text(str(value), x_start, HALF_HEIGHT, scale = NUMBER_SCALE)
    display.update()
    
    
def can_adjust(which_one, rh_value, min_value, max_value, direction):
    global on_rh
    global low_rh
    if direction == "up":
        if rh_value >= max_value:
            return False
        if which_one == "low" and rh_value >= on_rh:
            return False
    else:
        if rh_value <= min_value:
            return False
        if which_one == "on" and rh_value <= low_rh:
            return False
    return True


def choose_RH(which_one, min_value, max_value):
    global a_pressed
    global b_pressed
    global x_pressed
    global y_pressed
    global last_button_press_secs
    global on_rh
    global low_rh
    
    keep_processing = True
    rh_value = 0
    if which_one == "on":
        rh_value = on_rh
    else:
        rh_value = low_rh
    
    # clear a button press
    time.sleep(0.1)
    a_pressed = False
    
    while keep_processing:
        show_setting(rh_value)
        
        if a_pressed:
            if which_one == "on":
                on_rh = rh_value
            else:
                low_rh = rh_value
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            a_pressed = False
            return True
            
        if b_pressed:
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            b_pressed = False
            return True
            
        if x_pressed:
            if can_adjust(which_one, rh_value, min_value, max_value, "up"):
                rh_value = rh_value + 1
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            x_pressed = False

        if y_pressed:
            if can_adjust(which_one, rh_value, min_value, max_value, "down"):
                rh_value = rh_value - 1
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            y_pressed = False

        time.sleep(0.1)
        if time.time() - last_button_press_secs > MENU_IDLE_SECS_EXIT:
            return False

    
#
# Display the code version
#
def show_version():
    global a_pressed
    global b_pressed
    global x_pressed
    global y_pressed
    global last_button_press_secs
    
    keep_processing = True
    
    # Show the version string
    display.set_pen(BLACK)
    display.clear()
    
    display.set_pen(RED)
    display.set_font("sans")
    text_width = display.measure_text(VERSION, VERSION_SCALE)
    x_start = int( HALF_WIDTH - (text_width/2))
    display.text(VERSION, x_start, HALF_HEIGHT, scale = VERSION_SCALE)
    display.update()
    
    # clear a button press
    time.sleep(0.1)
    a_pressed = False
    
    while keep_processing:
        
        if a_pressed:
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            a_pressed = False
            return True
            
        if b_pressed:
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            b_pressed = False
            return True
            
        if x_pressed:
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            x_pressed = False

        if y_pressed:
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            y_pressed = False

        time.sleep(0.1)
        if time.time() - last_button_press_secs > MENU_IDLE_SECS_EXIT:
            return False

    
def enter_menu(current_menu, menu_context):
    global a_pressed
    global b_pressed
    global x_pressed
    global y_pressed
    global last_button_press_secs
    stay_in_menu = True

    # clear a button press
    time.sleep(0.1)
    a_pressed = False
    b_pressed = False
    x_pressed = False
    y_pressed = False
    
    menu_selection = 0

    last_button_press_secs = time.time()
    
    while stay_in_menu:
        menu_selection = show_menu_entries(current_menu, menu_selection)
        
        if a_pressed:
            action = current_menu[menu_selection]["action"]
            if action == "humidifier_off":
                log_message("action %s for humidifier %d" % (action, menu_context))
                humidifier_setting(humidifiers[menu_context], "off")
                # update last button press time
                time.sleep(0.1)
                last_button_press_secs = time.time()
                a_pressed = False
                return False
            elif action == "humidifier_lo":
                log_message("action %s for humidifier %d" % (action, menu_context))
                humidifier_setting(humidifiers[menu_context], "lo")
                # update last button press time
                time.sleep(0.1)
                last_button_press_secs = time.time()
                a_pressed = False
                return False
            elif action == "humidifier_hi":
                log_message("action %s for humidifier %d" % (action, menu_context))
                humidifier_setting(humidifiers[menu_context], "hi")
                # update last button press time
                time.sleep(0.1)
                last_button_press_secs = time.time()
                a_pressed = False
                return False
            elif action == "show_humidifier_menu_1":
                stay_in_menu = enter_menu(HUMIDIFIER_MENU, 0)
            elif action == "show_humidifier_menu_2":
                stay_in_menu = enter_menu(HUMIDIFIER_MENU, 1)
            elif action == "show_humidifier_menu_3":
                stay_in_menu = enter_menu(HUMIDIFIER_MENU, 2)
            elif action == "humidifiers_refilled":
                for i in range(len(humidifiers)):
                    humidifier_refilled(humidifiers[i])
                stay_in_menu = False
            elif action == "show_settings_menu":
                stay_in_menu = enter_menu(SETTINGS_MENU, None)
            elif action == "show_version":
                stay_in_menu = show_version()
            elif action == "show_settings_menu_on":
                stay_in_menu = choose_RH("on", 10, 95)
            elif action == "show_settings_menu_low":
                stay_in_menu = choose_RH("low", 10, 95)
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            a_pressed = False

        elif b_pressed:
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            b_pressed = False
            return True

        elif x_pressed:
            menu_selection = menu_selection - 1
            menu_selection = show_menu_entries(current_menu, menu_selection)
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            x_pressed = False

        elif y_pressed:
            menu_selection = menu_selection + 1
            menu_selection = show_menu_entries(current_menu, menu_selection)
            # update last button press time
            time.sleep(0.1)
            last_button_press_secs = time.time()
            y_pressed = False
            
        else:
            a_pressed = False
            b_pressed = False
            x_pressed = False
            y_pressed = False

        time.sleep(0.1)
        if time.time() - last_button_press_secs > MENU_IDLE_SECS_EXIT:
            break
        
    return
#
#######################################################
################ END MENU #############################
#######################################################


#######################################################
################ BEGIN RH #############################
#######################################################
#
# Reads the current RH from the sensor.  It does the following FOR EACH READING
#   Powers on the sensor
#   Waits 500ms for it to power up
#   Reads the temperture (ignored) and humidity
#   Powers off the sensor
#
# It reads RH_SAMPLES_PER_READ readings 1 second apart and returns the average.
#
def read_humidity():
    global sensor_power_pin

    humidity_total = 0.0
    humidity_count = 0
    
    # average 5 readings a second apart
    for i in range(0, RH_SAMPLES_PER_READ):
        log_message("reading sample %d" % i)
        if sensor_power_pin.value() == 1:
            log_message("sensor power on.  Turning off and sleeping 500ms")
            led_rgb(255,255,0) # yellow
            sensor_power_pin.value(0)
            clear_led()
            time.sleep_ms(500)

        #log_message("Enabling sensor power")
        led_rgb(255,255,0) # yellow
        sensor_power_pin.value(1)
        clear_led()

        #log_message("Sleeping 500ms for sensor to wake up")
        time.sleep_ms(500)

        #log_message("Creating dht20")
        led_rgb(0,0,255) #blue
        dht20 = DHT20(i2c)
        led_rgb(255,0,255) # magenta
        #log_message("Reading dht20 temperature")
        temperature = dht20.dht20_temperature()
        temperature = (temperature * 9.0 / 5.0 ) + 32.0
        #log_message("Reading dht20 humidity")
        led_rgb(0,255,255) # cyan
        humidity = dht20.dht20_humidity()
        #log_message("read temperature : %.4f, humidity : %.4f" % (temperature, humidity))

        #log_message("De-powering sensor")
        led_rgb(255,255,0) #yellow
        sensor_power_pin.value(0)
        
        humidity_total = humidity_total + humidity
        humidity_count = humidity_count + 1
        if humidity_count < RH_SAMPLES_PER_READ:
            #log_message("sleeping between RH readings")
            time.sleep(1)
    
    humidity = humidity_total / humidity_count
    log_message("reporting humidify of %.4f" % humidity)
    clear_led()
    return round(humidity, 2)


# Fake the RH instead of reading a sensor
def fake_rh():
    global fake_rh_ascending
    global fake_rh_hi
    global fake_rh_low
    global current_rh
    global rh_trend
    global should_refresh_display

    log_message("Faking humidity...")
    if fake_rh_ascending:
        if current_rh >= fake_rh_hi:
            fake_rh_ascending = False
            rh_trend = 0
            current_rh = current_rh - fake_rh_step
        else:
            current_rh = current_rh + fake_rh_step
            rh_trend = 1
        
    else: #descending
        if current_rh <= fake_rh_low:
            fake_rh_ascending = True
            rh_trend = 0
            current_rh = current_rh + fake_rh_step
        else:
            current_rh = current_rh - fake_rh_step
            rh_trend = -1
    record_rh(current_rh)
    log_message("RH now %.1f" % current_rh)        
    should_refresh_display = True


#
# Keep a rolling buffer of RH readings
#
def record_rh(rh):
    global prev_rh_readings
    
    for i in range(0, len(prev_rh_readings) - 1):
        prev_rh_readings[i] = prev_rh_readings[i+1]
    prev_rh_readings[len(prev_rh_readings)-1] = rh


#
#
#
def calculate_rh_trend():
    global prev_rh_readings
    
    # calculate average of the olde readings
    older_sum = 0
    older_count = 0
    for i in range(len(prev_rh_readings) - RH_READINGS_TO_TREND * 2, len(prev_rh_readings) - RH_READINGS_TO_TREND):
        if prev_rh_readings[i] > 0:
            older_sum = older_sum + prev_rh_readings[i]
            older_count = older_count + 1
    # if there aren't older readings, consider it level trend
    if older_count == 0:
        log_message("Too few RH readings to trend.")
        return 0
    # calculate the average
    older_avg = older_sum / older_count
        
    # calculate average of the newest 4 readings
    newest_sum = 0
    newest_count = 0
    for i in range(len(prev_rh_readings) - RH_READINGS_TO_TREND, len(prev_rh_readings)):
        if prev_rh_readings[i] > 0:
            newest_sum = newest_sum + prev_rh_readings[i]
            newest_count = newest_count + 1
    # calculate the average
    newest_avg = newest_sum / newest_count
    
    # based the trend on the differences between the averages
    trend_delta = newest_avg - older_avg
    if trend_delta < -0.2:
        trend = -1
    elif trend_delta > 0.2:
        trend = 1
    else:
        trend = 0
    log_message("RH oldest avg = %.4f, newest avg = %.4f, trend_delta=%.4f, trend=%d" % (older_avg, newest_avg, trend_delta, trend))
    return trend


#
# Update the current RH
#
def update_rh():
    global current_rh
    global rh_trend
    global should_refresh_display

    if FAKE_RH:
        fake_rh()
        return

    log_message("Reading humidity from sensor")
    successful_read = False
    while not successful_read:
        try:
            log_message("Attempting read")
            current_rh = read_humidity()
            log_message("Successful read")
            successful_read = True
        except OSError as err:
            log_message("OS error: {0}".format(err))
            log_message("##### Exception reading humidity.")
            time.sleep(1)

    record_rh(current_rh)
    
    rh_trend = calculate_rh_trend()
    log_message("RH now %.2f, trend %d" % (current_rh, rh_trend))
        
    should_refresh_display = True
#
#######################################################
################# END RH ##############################
#######################################################


# Draw the heartbeat circle in either black or blue to blink heartbeat circle
def toggle_heartbeat():
    global heartbeat_on
    
    if heartbeat_on:
        display.set_pen(BLACK)
    else:
        display.set_pen(BLUE)
    display.circle(HEARTBEAT_X, HEARTBEAT_Y, HEARTBEAT_CIRCLE_SIZE)
    display.update()
    heartbeat_on = not heartbeat_on


# Fake humidifier usage faster than reality
def fake_humidifier_use(humidifier):
    global humidifying
    if humidifying == "off":
        return
    if humidifier["setting"] == "off":
        return
    if not humidifier["energized"]:
        return
    if humidifier["setting"] == "lo":
        #log_message("Fake using humidifier %d lo_secs" % humidifier["outlet"])
        humidifier["lo_secs"] = humidifier["lo_secs"] + 15
    else:
        #log_message("Fake using humidifier %d hi_secs" % humidifier["outlet"])
        humidifier["hi_secs"] = humidifier["hi_secs"] + 15


#
# main
#

last_display_time = 0
last_rh_update_time = 0
last_heartbeat_ms = time.ticks_ms()
last_automate_time = time.time() - AUTOMATE_SECS + 5 # give 5 seconds before automating

display_error_text("Initializing...")
time.sleep(1)

try:
    while True:
        
        # If a is pressed, enter the menu
        if a_pressed:
            led_red()
            menu_selection = 0
            enter_menu(TOP_MENU, None)
            last_display_time = 0
            clear_led()

        # update RH at the appropriate interval
        if time.time() - last_rh_update_time > RH_UPDATE_SECS:
            update_rh()
            last_rh_update_time = time.time()

        # fake humidifier use
        #for i in range(len(humidifiers)):
        #    fake_humidifier_use(humidifiers[i])
        #    pct_used = calculate_pct_used(humidifiers[i])
        #    if pct_used >= 100.0:
        #        humidifier_refilled(humidifiers[i])

        # automate
        if time.time() - last_automate_time > AUTOMATE_SECS:
            automate_energizing()
            last_automate_time = time.time()

        # update humidifier bars at the appropriate interval
        if time.time() - last_display_time > BAR_DISPLAY_SECS or should_refresh_display:
            display_humidifier_bars()
            should_refresh_display = False
            last_display_time = time.time()

        # toggle the heartbeat as needed
        if time.ticks_diff(time.ticks_ms(), last_heartbeat_ms) >= HEARTBEAT_MS:
            toggle_heartbeat()
            last_heartbeat_ms = time.ticks_ms()

        # don't spin too fast
        time.sleep(0.1)
    
except BaseException as err:
    display_error_text(f"Unexpected {err=}, {type(err)=}")
    sys.print_exception(err)
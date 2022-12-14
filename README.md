# pico_humidity_controller
Pico controller for plug-in humidifiers.

The essential operation of this controller is to control up to 3 plug-in humidifiers in an attempt to keep the humidify at or above a certain level.
It does this by monitoring the humidity using a sensor and energizing pulg-in Vicks Warm-Mist humidifiers as needed to maintain the preferred humidity level.
It does not alter the setting of the plugged in humidifiers, it simply energizes or deenergizes each humidifier outlet as necessary.

<b>Settings</b>

Settings for the controller are managed via menus controlled by the buttons on the display.  The following settings are available:
* Setting of the humidifier plugged into outlet 1 - off, low, or high
* Setting of the humidifier plugged into outlet 2 - off, low or high
* Setting of the humidifier plugged into outlet 3 - off, low or high
* Relative humidity On threshold
* Relative humidity Low threshold
* There is also a menu selection to indicate the humidifier tanks have been refilled

<b>Operation</b>

It tracks remaining humidifier capacity by tracking how much time each humidifier has been run at each setting.
It expects these humidifiers will empty their tanks in 12 hours if run at high and 24 hours if run at low.
It considers the humidifiers refilled when that selection is made on in the menu.

When the humidity level crosses a threshold value, it must pass it by 0.5% before it it considered to have crossed it.
This is to prevent a humidity level very near a threshold value from causing frequent switching bewteen off, low and high levels.

When the humidity is higher than the On threshold, all outlets are deenergized.
They remain deenergized as long as the humidity is above the On threshold.

When the humidity is higher than the Low threshold but below the On threshold, it will energize a single humidifier.
In choosing a humidifier to energize, it will use the humidifier on a Low setting with the most capacity remaining.
When running in this state, if there are multiple humidifiers set to Low and the currently energized one has 20% or more less capacity than another Low humidifier, the controller will switch to the higher capacity Low humidifier.
This balances out the humidifier use.

When the humidity is below the Low threshold, the controller energized all humidifiers.
All humidifiers will remain energized until the humidity level rises above the Low threshold.

<b>Display</b>

<img src="humidifier_display.jpg" width=400>

Here is a description of the display.

Upper left corner shows a flashing ball.  It flashes at one of 3 speeds:
* every 2 seconds means the humidity is high enough and no humidifiers are energized.
* every 1 second means the humidity is below the On threshold and above the Low threshold, so light humidifying is occurring.
* every half second means the humidity is below the Low threshold, so heavy humidifying is occurring.

The upper half of the display shows the current relative humidity (54.9% in the image), followed by a trend arrow.
* up arrow indicates the humidity is rising
* level arrow indicates the humidity is steady
* down arrow indicates the humidity is falling (shown in image)

Behind the relative humidity display is a line giving historical humidity readings.
There are tick marks indicating every 2 hours.
The color of the line indicates:
* green - no humidifying occurring
* yellow - light humidifying occurring
* red - heavy humidifying occurring

The lower half of the display shows the three humidifiers.
A wide bar (83 in the image) is a humidifier set to High and a skinny bar (22 and 8 in the image) is a humidifier set to Low.
The color of the bar indicates:
* green - greater than 30% capacity remaining (83 in the image)
* yellow - between 10% and 30% capacity remaining (22 in the image)
* red - less than 10% capacity remaining (8 in the image)
The height of the bar also shows capacity remaining.

A lightning bolt on the bar indicates that humidifier is currently energized.
In the image, all three humidifiers are energized.

<b>Menu</b>

The menu is navigated using the 4 buttons on the display - A, B, X and Y.
They perform the following functions:
* A - enter menu or select item
* B - return up a level in the menu
* X - up
* Y - down

The menus are:

Main Menu
* Refill - select to indicate the humidifier tanks have been refilled
* Humidifier 1 2 or 3
* * OFF - humidifier is switched off
* * LO - humidifier is set to Low
* * HI - humidifier is set to High
* RH Settings
* * ON RH% - adjust the On relative humidity threshold
* * LOW RH% - adjust the Low relative humidity threshold
* Version - show the microcode version running

<b>Components</b>
* Raspberry Pi Pico
* Pimoroni Display Pack
* DHT22 Humidity & Temperature Sensor
* 1N4007 diode - quantitiy 3
* 2N3904 transistor - quantity 3
* 220 ohm 1/4W resistor - quantity 6
* LED of preferred color - quantity 3
* DC 5V Coil SPDT 5 Pins Mini PCB Power Relay JQC 3FF T73-5P-5V-B - quantity 3
* Micro-USB cable to power Pico
* USB pigtail for providing 5V power to relays
* Double USB power supply with shared ground
* 120V ungrounded outlet - quantity 3
* Packing of your choice to hold outlets (e.g. gang box)

<b>Schematic</b>

<img src="humidifier-controller.png">

The right hand side of the schematic is simpler than it appears.
The display mounts to the Pico pins, so the wiring occurs via that mount.

The relay board has 3 sets of the resistors, transistors, diodes, LEDs and relays.

For the mains power, the neutral (white) goes directly to the outlets.
The hot (black) goes through the relays.

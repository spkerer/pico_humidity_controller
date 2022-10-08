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

<img src="IMG_4955.JPG" width=400>

Here is a description of the display.

Upper left corner shows a flashing ball.  It flashes at one of 3 speeds:
* every 2 seconds means the humidity is high enough and no humidifiers are energized.
* every 1 second means the humidity is below the On threshold and above the Low threshold, so light humidifying is occurring.
* every half second means the humidity is below the Low threshold, so heavy humidifying is occurring.

The upper half of the display shows the current relative humidity (54.9% in the image), followed by a trend arrow.
* up arrow indicates the humidity is rising (shown in the image)
* level arrow indicates the humidity is steady
* down arrow indicates the humidity is falling

Behind the relative humidity display is a line giving historical humidity readings.
There are tick marks indicating every 2 hours.
The color of the line indicates:
* green - no humidifying occurring
* yellow - light humidifying occurring
* red - heavy humidifying occurring

The lower half of the display shows the three humidifiers.
A wide bar (47 in the image) is a humidifier set to High and a skinny bar (15 and 8 in the image) is a humidifier set to Low.
The color of the bar indicates:
* green - greater than 30% capacity remaining (47 in the image)
* yellow - between 10% and 30% capacity remaining (15 in the image)
* red - less than 10% capacity remaining (8 in the image)
The height of the bar also shows capacity remaining.

A lightning bolt on the bar indicates that humidifier is currently energized.
In the image, all three humidifiers are energized.

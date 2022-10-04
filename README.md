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

To be completed.

# led_ws281x_walker

## Installation

### Required python libs

```
pip install rpi-ws281x
pip install pyyaml
```

## Configuration

You can offer a YAML configuration file in the following format:

```YAML
led:
  count: 90 # Count of leds the strip has
  count_per_meter: 60 # Count of leds per meter (Used for speed calculation)
  pin: 18  # GPIO pin connected to the pixels (18 uses PWM!).
  freq_hz: 800000  # LED signal frequency in hertz (usually 800khz)
  dma: 0  # DMA channel to use for generating signal (try 10)
  brightness: 255  # Set to 0 for darkest and 255 for brightest
  invert: False  # True to invert the signal (when using NPN transistor level shift)
  channel: 0 # Channel of the led strip
```

## Running

The app is separated into a *led strip runner* and *walker generators*. The led strip runner is a loop updating the led strip; it watches on a directory for new walkers, adds them to active walkers and handles them in the loop. Walker generators, as the name says, generate walkers based on several ideas, e.g., there is a random monster drawer and an webservice adapter which offers an API to receive walkers. 

```
# Run the led strip runner
python led_strip_runner.py
# Run the monster drawer
python random_monster_draw_runner.py
```

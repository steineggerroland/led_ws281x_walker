# led_ws281x_walker

## Installation

### Required python libs

* [rpi-ws281x](https://github.com/rpi-ws281x/rpi-ws281x-python)
* [pyyaml](https://github.com/yaml/pyyaml)

#### Install rpi-ws281x requirements

_*gcc* and *python3-dev* need to be installed which can be achieved on debian based systems with the following instructions:_

```
sudo apt install gcc python3-dev
```

#### Install python libs using [pip](https://pypi.org/project/pip/)

_Please refer to [pip documentation for installation instructions](https://pip.pypa.io/en/stable/installation/)._

```
pip install rpi-ws281x
pip install pyyaml
```

### System.d service

You can setup a simple system.d service, to make sure the runner or one of the generators are up. Service files for these scripts exist and can be installed with the following commands.


```
sudo ln -s /<path to script>/<service file, e.g. led_strip_runner.service> /lib/systemd/system/<service file>
sudo systemctl daemon-reload
sudo systemctl enable <service file>
sudo systemctl start <service file>
```

## Configuration

You can offer a [YAML configuration file](https://yaml.org/) in the following format:

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
import colorsys
import json
import os
from os import walk, path

import yaml
import time
from rpi_ws281x import ws, Color, Adafruit_NeoPixel
import argparse
from led_strip_types import StripAdapter
from time import sleep, time
from threading import Thread, Lock

# Process arguments
parser = argparse.ArgumentParser()
parser.add_argument('-w', '--warm-colors', action='store_true',
                    help='use random warm colors')
parser.add_argument('-n', '--night-mode', action='store_true',
                    help='turn night mode on. warm colors and slow movement')
parser.add_argument('-W', '--no-whites', action='store_true',
                    help='just colors no white')
parser.add_argument('-c', '--led-configuration-file',
                    help='path to led configuration yaml')
parser.add_argument('-f', '--frame',
                    help='frame (from 0-4) to show changes. needed when having more led strips to sync their updates',
                    default=0, type=int, choices=range(0, 5))
args = parser.parse_args()
warm_colors = args.warm_colors or args.night_mode
slow_movement = args.night_mode
no_whites = args.no_whites or args.night_mode
# The LED strip is updated every 40ms (25 frames per second). The LED start flickering when updating the strip too fast
# (approximately faster than every 10ms). If you want to run several LED runners, they have to be synced to avoid
# flickering. Runners must use different frames.
time_offset = args.frame * .01

# LED strip configuration:
LED_COUNT = DEFAULT_LED_COUNT = 210
LED_COUNT_PER_METER = DEFAULT_LED_COUNT_PER_METER = DEFAULT_LED_COUNT / 3.5
LED_PIN = DEFAULT_LED_PIN = 13  # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = DEFAULT_LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = DEFAULT_LED_DMA = 14  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = DEFAULT_LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = DEFAULT_LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = DEFAULT_LED_CHANNEL = 1  # set to '1' for GPIOs 13, 19, 41, 45 or 53

if args.led_configuration_file:
    yaml_file = open(args.led_configuration_file, 'r')
    config = yaml.safe_load(yaml_file)
    LED_COUNT = config['led']['count'] if 'count' in config['led'] else DEFAULT_LED_COUNT
    LED_COUNT_PER_METER = config['led']['count_per_meter'] if 'count_per_meter' in config[
        'led'] else DEFAULT_LED_COUNT_PER_METER
    LED_PIN = config['led']['pin'] if 'pin' in config['led'] else DEFAULT_LED_PIN
    LED_FREQ_HZ = config['led']['freq_hz'] if 'freq_hz' in config['led'] else DEFAULT_LED_FREQ_HZ
    LED_DMA = config['led']['dma'] if 'dma' in config['led'] else DEFAULT_LED_DMA
    LED_BRIGHTNESS = config['led']['brightness'] if 'brightness' in config['led'] else DEFAULT_LED_BRIGHTNESS
    LED_INVERT = config['led']['invert'] if 'invert' in config['led'] else DEFAULT_LED_INVERT
    LED_CHANNEL = config['led']['channel'] if 'channel' in config['led'] else DEFAULT_LED_CHANNEL
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT,
                          LED_BRIGHTNESS, LED_CHANNEL, ws.WS2812_STRIP)
strip.begin()

TICK_LENGTH_IN_MS = 10  # values below 10 might lead to flickering leds
BACKGROUND_COLOR = Color(0, 0, 0, 0)
tick = 0


class Sequence:
    def __init__(self, sequence, position=0):
        self.sequence = sequence
        self.position = position
        self.current_glimmer = sequence[0]['glimmer']

    def handleTick(self):
        self.current_glimmer = self.sequence[tick % len(self.sequence)]['glimmer']
        if 'positionChange' in self.sequence[tick % len(self.sequence)]:
            self.position += self.sequence[tick % len(self.sequence)]['positionChange']

    def glimmer(self):
        return self.current_glimmer


def draw_monster(strip_to_draw_on, monster):
    old_position = monster.position
    old_glimmer = monster.glimmer()
    old_glimmer_positions = set(old_glimmer.keys())
    monster.handleTick()
    for position, glimmer in monster.glimmer().items():
        strip_to_draw_on.setPixelColor(monster.position + position, glimmer)
        if position + (monster.position - old_position) in old_glimmer_positions:
            old_glimmer_positions.remove(position + (monster.position - old_position))
    for position in old_glimmer_positions:
        strip_to_draw_on.removePixelColor(old_position + position, old_glimmer[position])


def reset(color):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    # wait until next frame of led strip to draw in
    sleep((.04 - (time() - time_offset) % .04))
    strip.show()


monsters = []
monster_lock = Lock()


def start():
    global tick
    reset(BACKGROUND_COLOR)
    strip_adapter = StripAdapter(strip, LED_COUNT, LED_COUNT_PER_METER, BACKGROUND_COLOR)
    while True:
        next_tick(monsters, strip_adapter)
        # wait until next frame of led strip to draw in
        sleep((.04 - (time() - time_offset) % .04))
        strip_adapter.show()
        tick += 1


def next_tick(monsters_to_draw, strip_to_draw_on):
    for monster in monsters_to_draw:
        if monster.position > strip_to_draw_on.led_count + len(monster.glimmer()):
            monster_lock.acquire()
            monsters_to_draw.remove(monster)
            monster_lock.release()
        else:
            draw_monster(strip_to_draw_on, monster)


monster_dir = 'new_monsters'


def draw_new_monsters():
    while True:
        # spawn monster at certain chance
        for path_name, subdirs, files in walk(monster_dir):
            for file_name in files:
                if file_name.endswith('.swp'):
                    continue
                monster_file = open(f"{monster_dir}/{file_name}", "r")
                try:
                    sequence_json = json.loads(monster_file.read())
                    os.remove(f"{monster_dir}/{file_name}")
                    sequence = []
                    for step in sequence_json:
                        glimmer = step['glimmer']
                        new_glimmer = {}
                        for key, value in glimmer.items():
                            new_glimmer[int(key)] = value
                        sequence.append({'glimmer': new_glimmer})
                        if 'positionChange' in step:
                            sequence[len(sequence) - 1]['positionChange'] = step['positionChange']
                    s = Sequence(sequence)
                    s.handleTick()
                    s.position -= int(max(s.glimmer().items())[0])
                    monster_lock.acquire()
                    monsters.append(s)
                    monster_lock.release()
                    print(f"added sequence {file_name}")
                except:
                    print(f"failed loading sequence {file_name}")
                finally:
                    monster_file.close()
        sleep(1)


led_update_thread = Thread(target=start)
monster_draw_thread = Thread(target=draw_new_monsters)
try:
    led_update_thread.start()
    monster_draw_thread.start()
except KeyboardInterrupt:
    if monster_draw_thread.isAlive():
        monster_draw_thread.join()
    if led_update_thread.isAlive():
        led_update_thread.join()
    reset(BACKGROUND_COLOR)

import colorsys
import uuid
from os import mkdir, path
from curses import wrapper
import yaml
import time
from rpi_ws281x import ws, Color, Adafruit_NeoPixel
from random import random, gauss
from secrets import randbelow
import argparse
from led_strip_types import StripAdapter
from monster_types import SneakingDotMonster, CaterpillarMonster, DotMonster
from time import sleep, time
from threading import Thread, Lock

# Process arguments
parser = argparse.ArgumentParser()
DEFAULT_TIME_TO_SPAWN = 8
parser.add_argument('-w', '--warm-colors', action='store_true',
                    help='use random warm colors')
parser.add_argument('-n', '--night-mode', action='store_true',
                    help='turn night mode on. warm colors and slow movement')
parser.add_argument('-d', '--dimmed', action='store_true',
                    help='dimm it and do not be bright')
parser.add_argument('-t', '--mean-time-to-spawn',
                    help='set mean time to spawn monsters',
                    default=DEFAULT_TIME_TO_SPAWN, type=int, choices=range(1, 300))
args = parser.parse_args()
warm_colors = args.warm_colors or args.night_mode
slow_movement = args.night_mode
dimmed = args.night_mode or args.dimmed
mean_seconds_to_spawn = args.mean_time_to_spawn if not args.night_mode or not args.mean_time_to_spawn == DEFAULT_TIME_TO_SPAWN else 45


def random_monster(screen):
    if warm_colors:
        hue = (randbelow(3600) / 3601) * 60 / 360
        hue = hue if hue < 30 / 360 else 1 - hue
        saturation = 1
    else:
        hue = randbelow(3600) / 3601
        saturation = 1

    lightness = 0.05 if dimmed else max(min(gauss(0.4, 0.2), 0.5), 0.3)
    c = colorsys.hls_to_rgb(hue, lightness, saturation)
    color = [round(c[0] * 255), round(c[1] * 255), round(c[2] * 255),
             round(lightness * 255) if saturation < 0.04 else 0]
    dice = random()
    if dice > 3 / 5:
        speed = round(random() * 30) + 2
        speed = speed * 10 if slow_movement else speed
        monster_length = max(2, round(gauss(2, .8)))
        screen.addstr(f"new sneaking monster ({color},{speed})")
        return SneakingDotMonster(
            color, speed, random() * .75 + .25,
                          round(random() * 100) + 20, monster_length)
    elif dice > 1 / 5:
        speed = round(random() * 50) + 8
        speed = speed * 10 if slow_movement else speed
        monster_length = max(2, round(gauss(2, .8)))
        step_length = max(3, round(gauss(5, 1.5)))
        screen.addstr(f"new caterpillar monster ({color},{speed},{step_length})")
        return CaterpillarMonster(color, speed, monster_length, step_length)
    else:
        speed = round(random() * 10) + 2
        speed = speed * 10 if slow_movement else speed
        screen.addstr(f"new dot monster ({color},{speed})")
        return DotMonster(
            color, speed, random() * .5 + .2,
                          round(random() * 500) + 100)


monster_dir = 'new_monsters'
if not path.exists(monster_dir):
    mkdir(monster_dir)


def draw_new_monsters(screen):
    while True:
        # spawn monster at certain chance
        seconds_until_spawn = int(gauss(mean_seconds_to_spawn, mean_seconds_to_spawn * 0.666))
        while seconds_until_spawn > 0:
            screen.addstr(0, 0, f"Next monster in {seconds_until_spawn} seconds     ")
            screen.refresh()
            seconds_until_spawn -= 1
            sleep(1)
        screen.move(1, 0)
        screen.insertln()
        monster = random_monster(screen)
        with open(f"{monster_dir}/monster-{uuid.uuid4()}.json", 'w') as f:
            f.write(monster.json_sequence())
        screen.refresh()


def main(screen):
    monster_draw_thread = Thread(target=draw_new_monsters, args=(screen,))
    try:
        monster_draw_thread.start()
    except KeyboardInterrupt:
        if monster_draw_thread.isAlive():
            monster_draw_thread.join()

wrapper(main)

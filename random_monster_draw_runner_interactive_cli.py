import argparse
import uuid
from curses import wrapper
from os import mkdir, path
from random import gauss
from threading import Thread
from time import sleep

from monster_types import random_monster

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
        monster = random_monster(warm_colors, slow_movement, dimmed)
        screen.addstr(monster.description)
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

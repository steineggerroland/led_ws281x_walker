import math
import time
from rpi_ws281x import ws, Color, Adafruit_NeoPixel
from random import random, gauss
import colorsys
import argparse

# LED strip configuration:
LED_COUNT = 210
LED_COUNT_PER_METER = LED_COUNT / 3.5
LED_PIN = 13  # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 14  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 1  # set to '1' for GPIOs 13, 19, 41, 45 or 53
strip1 = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT,
                           LED_BRIGHTNESS, LED_CHANNEL, ws.WS2812_STRIP)
strip1.begin()

# LED strip configuration:
LED2_COUNT = 90
LED2_COUNT_PER_METER = LED2_COUNT / 1.5
LED2_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
LED2_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED2_DMA = 0  # DMA channel to use for generating signal (try 10)
LED2_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED2_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED2_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
strip2 = Adafruit_NeoPixel(LED2_COUNT, LED2_PIN, LED2_FREQ_HZ, LED2_DMA,
                           LED2_INVERT, LED2_BRIGHTNESS, LED2_CHANNEL,
                           ws.WS2812_STRIP)
strip2.begin()

TICK_LENGTH_IN_MS = 10  # values below 10 might lead to flickering leds
BACKGROUND_COLOR = Color(0, 0, 0, 0)

# Process arguments
parser = argparse.ArgumentParser()
parser.add_argument('-w', '--warm-colors', action='store_true',
                    help='use random warm colors')
parser.add_argument('-n', '--night-mode', action='store_true',
                    help='turn night mode on. warm colors and slow movement')
parser.add_argument('-W', '--no-whites', action='store_true',
                    help='just colors no white')
args = parser.parse_args()
warm_colors = args.warm_colors or args.night_mode
slow_movement = args.night_mode
no_whites = args.no_whites or args.night_mode


class Monster:
    def __init__(self, speed=1, position=0):
        self.speed = speed
        self.position = position

    def glimmer(self):
        return {}

    def handleTick(self, tick):
        if (tick % self.speed) == 0:
            self.position += 1


def random_monster():
    if warm_colors:
        hue = random() * 60 / 360
        hue = hue if hue < 30 / 360 else 1 - hue
        saturation = -1
    else:
        hue = random()
        saturation = -1 if no_whites or random() > .05 else 0

    lightness = 10 if saturation == -1 else 255
    c = colorsys.hls_to_rgb(hue, lightness, saturation)
    color = [round(c[0]), round(c[1]), round(c[2]),
             255 if saturation == 0 else 0]
    dice = random()
    if dice > 3 / 5:
        speed = round(random() * 30) + 2
        speed = speed * 10 if slow_movement else speed
        monster_length = max(2, round(gauss(2, .8)))
        return SneakingDotMonster(
            color, speed, random() * .75 + .25,
                          round(random() * 100) + 20, monster_length)
    elif dice > 1 / 5:
        speed = round(random() * 50) + 8
        speed = speed * 10 if slow_movement else speed
        monster_length = max(2, round(gauss(2, .8)))
        step_length = max(4, round(gauss(6, 1.5)))
        return CaterpillarMonster(color, speed, monster_length, step_length)
    else:
        speed = round(random() * 10) + 2
        speed = speed * 10 if slow_movement else speed
        return DotMonster(
            color, speed, random() * .5 + .2,
                          round(random() * 500) + 100)


class DotMonster(Monster):
    def __init__(self, color, speed=10, glow=.5, glow_speed=200, position=0):
        super().__init__(speed, position)
        self.glow = glow
        self.glow_speed = glow_speed
        self.base_color = color
        self.base_hls = colorsys.rgb_to_hls(color[0], color[1], color[2])
        self.color = Color(color[0], color[1], color[2],
                           color[3] if color[3] else 0)

    def handleTick(self, tick):
        variance = 2 * self.glow * divmod(tick, self.glow_speed)[
            1] / self.glow_speed
        variance = 1 - variance if (self.glow) - variance > 0 else 1 - (
                2 * self.glow - variance)
        rgb = colorsys.hls_to_rgb(self.base_hls[0],
                                  max(0,
                                      min(255,
                                          round(self.base_hls[1] * variance))),
                                  self.base_hls[2])
        self.base_color = [round(rgb[0]),
                           round(rgb[1]),
                           round(rgb[2]),
                           max(0,
                               min(255, round(self.base_color[3] * variance)))]
        self.color = Color(self.base_color[0], self.base_color[1],
                           self.base_color[2], self.base_color[3])
        if (tick % self.speed) == 0:
            self.position += 1

    def glimmer(self):
        return {0: self.color}


class SneakingDotMonster(DotMonster):
    def __init__(self, color, speed=10, glow=255, glow_speed=200, length=2):
        super().__init__(color, speed, glow, glow_speed, -length - 1)
        self.length = length
        self.current_glimmer = {}
        for pos in range(self.length):
            self.current_glimmer[pos] = self.color
        # precalculate glimmer for each tick
        self.glimmer_sequence = {}
        hls = colorsys.rgb_to_hls(self.base_color[0], self.base_color[1],
                                  self.base_color[2])
        for tick in range(speed):
            if (tick % self.speed) == 0:
                self.glimmer_sequence[tick] = {}
                for pos in range(self.length):
                    self.glimmer_sequence[tick][pos] = self.color
            else:
                sneak_tick = divmod(tick, self.speed)[1]
                self.glimmer_sequence[tick] = {}
                # draw head in movement
                g = sneak_tick / self.speed
                g = math.pow(g, 3)
                rgb = colorsys.hls_to_rgb(hls[0],
                                          max(0, min(255, round(g * hls[1]))),
                                          hls[2])
                color = Color(round(rgb[0]), round(rgb[1]), round(rgb[2]),
                              max(0, min(255, round(g * self.base_color[3]))))
                self.glimmer_sequence[tick][self.length] = color
                # draw body
                for pos in range(1, self.length):
                    self.glimmer_sequence[tick][pos] = Color(self.base_color[0],
                                                             self.base_color[1],
                                                             self.base_color[2],
                                                             self.base_color[3])
                # draw tail in movement
                if self.length > 1:
                    g = (self.speed - sneak_tick) / self.speed
                    g = math.pow(g, 3)
                    rgb = colorsys.hls_to_rgb(hls[0],
                                              max(0,
                                                  min(255, round(g * hls[1]))),
                                              hls[2])
                    color = Color(round(rgb[0]), round(rgb[1]), round(rgb[2]),
                                  max(0,
                                      min(255, round(g * self.base_color[3]))))
                    self.glimmer_sequence[tick][0] = color

    def handleTick(self, tick):
        self.current_glimmer = self.glimmer_sequence[tick % self.speed]
        if (tick % self.speed) == 0:
            self.position += 1

    def glimmer(self):
        return self.current_glimmer


class CaterpillarMonster(DotMonster):
    def __init__(self, color, speed=20, length=2, step_length=6):
        super().__init__(color, speed if speed % 2 == 1 else speed + 1, 0, 1,
                         -length - 1)
        self.step_length = step_length
        self.length = length
        self.current_glimmer = {}
        for pos in range(self.length):
            self.current_glimmer[pos] = self.color
        # precalculate glimmer for each tick
        self.glimmer_sequence = {}
        hls = colorsys.rgb_to_hls(self.base_color[0], self.base_color[1],
                                  self.base_color[2])
        # basic glimmer when standing
        self.glimmer_sequence[0] = {}
        for pos in range(self.length):
            self.glimmer_sequence[0][pos] = self.color
        # calculate glimmer in motion
        # spreading motion
        ticks_per_motion = math.floor(speed / 2)
        for tick in range(ticks_per_motion):
            spread_tick = divmod(tick, ticks_per_motion)[1]
            g = spread_tick / ticks_per_motion
            # assume color darkens linear when spreading down to .4 of max
            g = 1 - .8 * g
            rgb = colorsys.hls_to_rgb(hls[0],
                                      max(0, min(255, round(g * hls[1]))),
                                      hls[2])
            glimmer = {}
            for pos in range(round(self.length + (
                    spread_tick / ticks_per_motion) * self.step_length)):
                glimmer[pos] = Color(round(rgb[0]),
                                     round(rgb[1]),
                                     round(rgb[2]),
                                     self.base_color[3])
            self.glimmer_sequence[tick + 1] = glimmer
        for tick in range(ticks_per_motion):
            spread_tick = divmod(tick, ticks_per_motion)[1]
            g = spread_tick / ticks_per_motion
            # assume color lightens linear when shrinking up from .4 to max
            g = .2 + .8 * g
            rgb = colorsys.hls_to_rgb(hls[0],
                                      max(0, min(255, round(g * hls[1]))),
                                      hls[2])
            glimmer = {}
            current_length = round(self.length + ((
                                                          ticks_per_motion - spread_tick) / ticks_per_motion) * self.step_length)
            for pos in range(self.length + self.step_length - current_length,
                             self.length + self.step_length):
                glimmer[pos] = Color(round(rgb[0]),
                                     round(rgb[1]),
                                     round(rgb[2]),
                                     self.base_color[3])
            self.glimmer_sequence[tick + 1 + ticks_per_motion] = glimmer

    def handleTick(self, tick):
        self.current_glimmer = self.glimmer_sequence[tick % self.speed]
        if (tick % self.speed) == 0:
            self.position += self.step_length

    def glimmer(self):
        return self.current_glimmer


class StripAdapter:
    def __init__(self, strip, led_count, leds_per_meter, background_color):
        self.physical_strip = strip
        self.led_count = led_count
        self.leds_per_meter = leds_per_meter
        self.background_color = background_color

    def setPixelColor(self, position, color):
        if 0 < position < self.led_count:
            self.physical_strip.setPixelColor(position, color)

    def setPixelToBackground(self, position):
        if 0 < position < self.led_count:
            self.physical_strip.setPixelColor(position, self.background_color)

    def removePixelColor(self, position, color):
        if self.physical_strip.getPixelColor(position) == color:
            self.setPixelToBackground(position)

    def show(self):
        self.physical_strip.show()


def draw_monster(strip_to_draw_on, monster, tick):
    old_position = monster.position
    old_glimmer = monster.glimmer()
    monster.handleTick(tick)
    for position, glimmer in monster.glimmer().items():
        strip_to_draw_on.setPixelColor(monster.position + position, glimmer)
    for position in range(old_position,
                          monster.position + min(monster.glimmer().keys())):
        if old_glimmer.get(position - old_position):
            strip_to_draw_on.removePixelColor(position, old_glimmer[
                position - old_position])


def reset(strip, color):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()
    time.sleep(TICK_LENGTH_IN_MS / 1000.0)


def start():
    reset(strip1, BACKGROUND_COLOR)
    reset(strip2, BACKGROUND_COLOR)
    tick = 0
    strip1_adapter = StripAdapter(strip1, LED_COUNT, LED_COUNT_PER_METER,
                                  BACKGROUND_COLOR)
    monsters_strip1 = [random_monster()]
    strip2_adapter = StripAdapter(strip2, LED2_COUNT, LED2_COUNT_PER_METER,
                                  BACKGROUND_COLOR)
    monsters_strip2 = [random_monster()]
    while True:
        next_tick(monsters_strip1, strip1_adapter, tick)
        strip1_adapter.show()
        # there must be a delay of about 10 ms between two strip.show()
        time.sleep(10 / 1000)
        next_tick(monsters_strip2, strip2_adapter, tick)
        strip2_adapter.show()
        time.sleep(TICK_LENGTH_IN_MS / 1000.0)
        tick += 1


def next_tick(monsters, strip, tick):
    # spawn monster at certain chance
    chance = abs(
        gauss(0,
              ((strip.led_count / strip.leds_per_meter) * 4) / len(
                  monsters))) > 4
    if chance:
        monsters.append(random_monster())

    for monster in monsters:
        if monster.position > strip.led_count + len(monster.glimmer()):
            monsters.remove(monster)
        else:
            draw_monster(strip, monster, tick)
    strip.show()


try:
    start()
except KeyboardInterrupt:
    reset(strip1, BACKGROUND_COLOR)
    reset(strip2, BACKGROUND_COLOR)

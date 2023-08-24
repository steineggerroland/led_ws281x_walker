import colorsys
import json
import math
from random import random, gauss
from secrets import randbelow

from rpi_ws281x import Color


class Monster:
    def __init__(self, speed=1, position=0, description="a monster"):
        self.speed = speed
        self.position = position
        self.description = description

    def glimmer(self):
        return {}

    def handleTick(self, tick):
        if (tick % self.speed) == 0:
            self.position += 1

    def json_sequence(self):
        encoder = json.JSONEncoder()
        sequence = [{"glimmer": {}, "positionChange": 1}]
        return encoder.encode(sequence)


class DotMonster(Monster):
    def __init__(self, color, speed=10, glow=.5, glow_speed=200, position=0):
        super().__init__(speed, position, f"dot monster: color {color_to_text(color)}, speed {speed}")
        self.glow = glow
        self.glow_speed = glow_speed
        self.base_color = color
        self.base_hls = colorsys.rgb_to_hls(color[0] / 255, color[1] / 255, color[2] / 255)
        self.color = Color(color[0], color[1], color[2], color[3])
        # calculate glimmer sequence
        self.glimmer_sequence = {}
        for tick in range(self.speed * self.glow_speed):
            self.glimmer_sequence[tick] = {}
            variance = 2 * self.glow * divmod(tick, self.glow_speed)[
                1] / self.glow_speed
            variance = 1 - variance if self.glow - variance > 0 else 1 - (
                    2 * self.glow - variance)
            rgb = colorsys.hls_to_rgb(self.base_hls[0],
                                      self.base_hls[1] * variance,
                                      self.base_hls[2])
            base_color = [round(rgb[0] * 255),
                          round(rgb[1] * 255),
                          round(rgb[2] * 255),
                          max(0,
                              min(255, round(self.base_color[3] * variance)))]
            color = Color(base_color[0], base_color[1],
                          base_color[2], base_color[3])
            self.glimmer_sequence[tick][0] = color

    def handleTick(self, tick):
        variance = 2 * self.glow * divmod(tick, self.glow_speed)[
            1] / self.glow_speed
        variance = 1 - variance if self.glow - variance > 0 else 1 - (
                2 * self.glow - variance)
        rgb = colorsys.hls_to_rgb(self.base_hls[0],
                                  self.base_hls[1] * variance,
                                  self.base_hls[2])
        self.base_color = [round(rgb[0] * 255),
                           round(rgb[1] * 255),
                           round(rgb[2] * 255),
                           max(0,
                               min(255, round(self.base_color[3] * variance)))]
        self.color = Color(self.base_color[0], self.base_color[1],
                           self.base_color[2], self.base_color[3])
        if (tick % self.speed) == 0:
            self.position += 1

    def glimmer(self):
        return {0: self.color}

    def json_sequence(self):
        encoder = json.JSONEncoder()
        sequence = []
        for key, value in self.glimmer_sequence.items():
            sequence.append({"glimmer": value})
            if key % self.speed == 0:
                sequence[len(sequence) - 1]["positionChange"] = 1
        return encoder.encode(sequence)


class SneakingDotMonster(Monster):
    def __init__(self, color, speed=10, glow=255, glow_speed=200, length=2):
        super().__init__(speed, -length - 1, f"sneaking monster: color {color_to_text(color)}, speed {speed}")
        self.glow = glow
        self.glow_speed = glow_speed
        self.base_color = color
        self.color = Color(color[0], color[1], color[2], color[3])
        self.length = length
        self.current_glimmer = {}
        for pos in range(self.length):
            self.current_glimmer[pos] = self.color
        # precalculate glimmer for each tick
        self.glimmer_sequence = {}
        hls = colorsys.rgb_to_hls(self.base_color[0] / 255, self.base_color[1] / 255,
                                  self.base_color[2] / 255)
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
                                          g * hls[1],
                                          hls[2])
                color = Color(round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255),
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
                                              g * hls[1],
                                              hls[2])
                    color = Color(round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255),
                                  max(0,
                                      min(255, round(g * self.base_color[3]))))
                    self.glimmer_sequence[tick][0] = color

    def handleTick(self, tick):
        self.current_glimmer = self.glimmer_sequence[tick % self.speed]
        if (tick % self.speed) == 0:
            self.position += 1

    def glimmer(self):
        return self.current_glimmer

    def json_sequence(self):
        encoder = json.JSONEncoder()
        sequence = []
        for key, value in self.glimmer_sequence.items():
            sequence.append({"glimmer": value})
        sequence[0]["positionChange"] = 1
        return encoder.encode(sequence)


class CaterpillarMonster(Monster):
    def __init__(self, color, speed=20, length=2, step_length=6):
        super().__init__(speed if speed % 2 == 1 else speed + 1, -length - 1,
                         f"caterpillar monster: color {color_to_text(color)}, speed {speed},"
                         f" step length {step_length})")
        self.glow = 0
        self.glow_speed = 1
        self.base_color = color
        self.color = Color(color[0], color[1], color[2], color[3])
        self.step_length = step_length
        self.length = length
        self.current_glimmer = {}
        for pos in range(self.length):
            self.current_glimmer[pos] = self.color
        # precalculate glimmer for each tick
        self.glimmer_sequence = {}
        hls = colorsys.rgb_to_hls(self.base_color[0] / 255, self.base_color[1] / 255,
                                  self.base_color[2] / 255)
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
                                      g * hls[1],
                                      hls[2])
            glimmer = {}
            for pos in range(round(self.length + (
                    spread_tick / ticks_per_motion) * self.step_length)):
                glimmer[pos] = Color(round(rgb[0] * 255),
                                     round(rgb[1] * 255),
                                     round(rgb[2] * 255),
                                     self.base_color[3])
            self.glimmer_sequence[tick + 1] = glimmer
        for tick in range(ticks_per_motion):
            spread_tick = divmod(tick, ticks_per_motion)[1]
            g = spread_tick / ticks_per_motion
            # assume color lightens linear when shrinking up from .4 to max
            g = .2 + .8 * g
            rgb = colorsys.hls_to_rgb(hls[0],
                                      g * hls[1],
                                      hls[2])
            glimmer = {}
            current_length = round(self.length + ((
                                                          ticks_per_motion - spread_tick) / ticks_per_motion) * self.step_length)
            for pos in range(self.length + self.step_length - current_length,
                             self.length + self.step_length):
                glimmer[pos] = Color(round(rgb[0] * 255),
                                     round(rgb[1] * 255),
                                     round(rgb[2] * 255),
                                     self.base_color[3])
            self.glimmer_sequence[tick + 1 + ticks_per_motion] = glimmer

    def handleTick(self, tick):
        self.current_glimmer = self.glimmer_sequence[tick % self.speed]
        if (tick % self.speed) == 0:
            self.position += self.step_length

    def glimmer(self):
        return self.current_glimmer

    def json_sequence(self):
        encoder = json.JSONEncoder()
        sequence = []
        for key, value in self.glimmer_sequence.items():
            sequence.append({"glimmer": value})
        sequence[0]["positionChange"] = self.step_length
        return encoder.encode(sequence)


class SprintMonster(Monster):
    def __init__(self, color, sprint_distance=20, recovery_time=20, position=0):
        self.sprint_distance = max(1, sprint_distance)
        self.recovery_time = max(1, recovery_time)
        super().__init__(self.sprint_distance + self.recovery_time,
                         min(position % self.sprint_distance, self.sprint_distance),
                         f"sprinter: color {color_to_text(color)}, sprinting distance {self.sprint_distance} "
                         f"and recovery time {self.recovery_time}")
        self.base_color = color
        self.base_hls = colorsys.rgb_to_hls(color[0] / 255, color[1] / 255, color[2] / 255)
        self.color = Color(color[0], color[1], color[2], color[3])
        self.current_glimmer = self.color
        # calculate glimmer sequence
        self.glimmer_sequence = {}
        # sprinters run each tick up to the sprint distance, thus add 1 for each tick
        for tick in range(self.sprint_distance):
            self.glimmer_sequence[tick] = {}
            self.glimmer_sequence[tick][tick] = self.color
        # sprinters are so fast, they create a (2 dot) trail while sprinting
        for tick in range(self.sprint_distance):
            if tick > 1:
                dim = .6
                rgb = colorsys.hls_to_rgb(self.base_hls[0],
                                          dim * self.base_hls[1],
                                          self.base_hls[2])
                color = Color(round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255),
                              max(0, min(255, round(dim * self.base_color[3]))))
                self.glimmer_sequence[tick][tick - 1] = color
            if tick > 2:
                dim = .3
                rgb = colorsys.hls_to_rgb(self.base_hls[0],
                                          dim * self.base_hls[1],
                                          self.base_hls[2])
                color = Color(round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255),
                              max(0, min(255, round(dim * self.base_color[3]))))
                self.glimmer_sequence[tick][tick - 2] = color
        # after running, sprinters have to recover energy for the next sprint
        for tick in range(self.recovery_time):
            dim = tick / self.recovery_time
            rgb = colorsys.hls_to_rgb(self.base_hls[0],
                                      dim * self.base_hls[1],
                                      self.base_hls[2])
            color = Color(round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255),
                          max(0, min(255, round(dim * self.base_color[3]))))
            self.glimmer_sequence[self.sprint_distance + tick] = {}
            self.glimmer_sequence[self.sprint_distance + tick][self.sprint_distance] = color

    def handleTick(self, tick):
        self.current_glimmer = self.glimmer_sequence[tick % self.speed]
        if (tick % self.speed) == 0:
            self.position += self.speed

    def glimmer(self):
        return self.current_glimmer

    def json_sequence(self):
        encoder = json.JSONEncoder()
        sequence = []
        for key, value in self.glimmer_sequence.items():
            sequence.append({"glimmer": value})
            if key % self.speed == 0:
                sequence[len(sequence) - 1]["positionChange"] = self.sprint_distance
        return encoder.encode(sequence)


def color_to_text(color):
    h = colorsys.rgb_to_hls(color[0] / 255, color[1] / 255, color[2] / 255)[0]
    if h < 10 / 360:
        return "red"
    elif h < 45 / 360:
        return "orange"
    elif h < 75 / 360:
        return "yellow"
    elif h < 150 / 360:
        return "green"
    elif h < 195 / 360:
        return "cyan"
    elif h < 255 / 360:
        return "blue"
    elif h < 285 / 360:
        return "violet"
    elif h < 315 / 360:
        return "magenta"
    elif h < 330 / 360:
        return "pink"
    else:
        return "red"


def random_monster(warm_colors, slow_movement, dimmed):
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
    if dice > 2 / 6:
        speed = round(random() * 30) + 2
        speed = speed * 10 if slow_movement else speed
        monster_length = max(2, round(gauss(2, .8)))
        return SneakingDotMonster(
            color, speed, round(random() * .75 + .25), round(random() * 100) + 20, monster_length)
    elif dice > 2 / 6:
        speed = round(random() * 50) + 8
        speed = speed * 10 if slow_movement else speed
        monster_length = max(2, round(gauss(2, .8)))
        step_length = max(3, round(gauss(5, 1.5)))
        return CaterpillarMonster(color, speed, monster_length, step_length)
    elif dice > 1 / 6:
        monster_length = max(2, round(gauss(2, .8)))
        return SprintMonster(color)
    else:
        speed = round(random() * 10) + 2
        speed = speed * 10 if slow_movement else speed
        return DotMonster(
            color, speed, random() * .5 + .2, round(random() * 500) + 100)

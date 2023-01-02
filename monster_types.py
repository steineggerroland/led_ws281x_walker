import colorsys
import json
import math
from rpi_ws281x import Color


class Monster:
    def __init__(self, speed=1, position=0):
        self.speed = speed
        self.position = position

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
        super().__init__(speed, position)
        self.glow = glow
        self.glow_speed = glow_speed
        self.base_color = color
        self.base_hls = colorsys.rgb_to_hls(color[0]/255, color[1]/255, color[2]/255)
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
        variance = 1 - variance if (self.glow) - variance > 0 else 1 - (
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


class SneakingDotMonster(DotMonster):
    def __init__(self, color, speed=10, glow=255, glow_speed=200, length=2):
        super().__init__(color, speed, glow, glow_speed, -length - 1)
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

import math
import time
from rpi_ws281x import ws, Color, Adafruit_NeoPixel
from random import random, gauss
import colorsys

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

TICK_LENGTH_IN_MS = 10
BACKGROUND_COLOR = Color(0, 0, 0, 0)


def reset(s1, s2, color):
    s1_pixel_count = s1.numPixels()
    s2_pixel_count = s2.numPixels()
    for i in range(s1_pixel_count):
        if i < s1_pixel_count:
            s1.setPixelColor(i, color)
            s1.show()
            time.sleep(TICK_LENGTH_IN_MS / 1000)
    for i in range(s2_pixel_count):
        if i < s2_pixel_count:
            s2.setPixelColor(i, color)
            s2.show()
            time.sleep(TICK_LENGTH_IN_MS / 1000)

reset(strip1, strip2, Color(0, 0, 0))


while False:
    reset(strip1, strip2, Color(255, 0, 0))
    reset(strip1, strip2, Color(0, 255, 0))
    reset(strip1, strip2, Color(0, 0, 255))

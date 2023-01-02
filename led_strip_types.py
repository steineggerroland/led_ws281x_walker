class StripAdapter:
    def __init__(self, strip, led_count, leds_per_meter, background_color):
        self.physical_strip = strip
        self.led_count = led_count
        self.leds_per_meter = leds_per_meter
        self.background_color = background_color

    def setPixelColor(self, position, color):
        if 0 <= position < self.led_count:
            self.physical_strip.setPixelColor(position, color)

    def setPixelToBackground(self, position):
        if 0 <= position < self.led_count:
            self.physical_strip.setPixelColor(position, self.background_color)

    def removePixelColor(self, position, color):
        if self.physical_strip.getPixelColor(position) == color:
            self.setPixelToBackground(position)

    def show(self):
        self.physical_strip.show()

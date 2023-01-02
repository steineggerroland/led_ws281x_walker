from http.server import BaseHTTPRequestHandler, HTTPServer
from rpi_ws281x import PixelStrip, Color
import json


# LED strip configuration:
LED_COUNT = 300  # Number of LED pixels.
LED_COUNT_PER_METER = LED_COUNT / 5  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT,
                   LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()
BACKGROUND_COLOR = Color(0, 0, 0, 0)


for i in range(strip.numPixels()):
  strip.setPixelColor(i, BACKGROUND_COLOR)
strip.show()


class Handler(BaseHTTPRequestHandler):

  def do_POST(self):
    length = int(self.headers.get('content-length'))
    message = json.loads(self.rfile.read(length))
    upload = message['upload']
    download = message['download']
    strip.setPixelColor(0, Color(upload, 0, download))
    for i in range(strip.numPixels(), -2, -1):
      strip.setPixelColor(i, strip.getPixelColor(i-1))
    strip.show()
    self.send_response(201)


# Bind to the local address only.
server_address = ('192.168.178.73', 8089)
httpd = HTTPServer(server_address, Handler)
print("Starting server...")
httpd.serve_forever()
print("Server stopped.")

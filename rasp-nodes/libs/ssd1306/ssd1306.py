# This example is for use on (Linux) computers that are using CPython with
# Adafruit Blinka to support CircuitPython libraries. CircuitPython does
# not support PIL/pillow (python imaging library)!

import subprocess
import time

import busio
from board import SCL, SDA
from PIL import Image, ImageDraw, ImageFont

import adafruit_ssd1306

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)

while True:
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    cmd = "hostname"
    HOST = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "hostname -I | cut -d' ' -f1"
    IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "systemctl is-active ssh"
    SSH_SERVICE = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    cmd = 'iw dev wlan0 link | awk \'/signal/ {sig=$2} /tx bitrate/ {rate=$3; printf "(wlan0): %s dBm  %s Mbit/s\\n", sig, rate}\''
    WIFI_RATE = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "w -h | wc -l"
    SSH_USERS = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d: -f2"
    SSID = subprocess.check_output(cmd, shell=True).decode("utf-8")

    draw.text((x, top + 0), "Host: " + HOST, font=font, fill=255)
    draw.text((x, top + 10), "IP: " + IP, font=font, fill=255)
    draw.text((x, top + 20), WIFI_RATE, ont=font, fill=255)
    draw.text((x, top + 30), "SSH: " + SSH_SERVICE, font=font, fill=255)
    draw.text((x, top + 40), "USERS: " +  SSH_USERS, font=font, fill=255)
    draw.text((x, top + 50), "SSID: " + SSID, font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.show()
    time.sleep(1)

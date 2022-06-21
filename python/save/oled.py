# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This demo will fill the screen with white, draw a black box on top
and then print Hello World! in the center of the display

This example is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!
"""

import time

from smbus import SMBus
import adafruit_ssd1306
import board
from PIL import Image, ImageDraw, ImageFont

# Define the Reset Pin
# oled_reset = digitalio.DigitalInOut(board.D4)

# Change these
# to the right size for your display!
WIDTH = 128
HEIGHT = 64  # Change to 64 if needed
BORDER = 2

i2cbus = SMBus(1)
i2c = board.I2C()

def init_disp():
    for i in range(0, 2):
        i2cbus.write_byte(0x70, 1 << i)
        oled.init_display()
        oled.show()

def display(number: int):
    print(f'{number:d}: select display')
    i2cbus.write_byte(0x70, 1 << number)

display(0)
time.sleep(0.1)
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3c)
init_disp()
display(0)

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new("1", (oled.width, oled.height))
empty = image.copy()

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a white background
# draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=255)
# draw.rectangle(
#     (BORDER, BORDER, oled.width - BORDER - 1, oled.height - BORDER - 1),
#     outline=0,
#     fill=0,
# )

# Load default font.
# font = ImageFont.load_default()
font_family = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
# DejaVuSansMono.ttf
# DejaVuSerif.ttf
font = ImageFont.truetype(font_family, 42)
font1 = ImageFont.truetype(font_family, 10)
font2 = ImageFont.truetype(font_family, 20)

# draw.text(
#     (oled.width // 2 - font_width // 2, oled.height // 2 - font_height // 2),
#     text,
#     font=font,
#     fill=255,
# )

MSG_BOOT = "Boot"
MSG_BOOT_FONT = font
(msg_boot_width, _) = MSG_BOOT_FONT.getsize(MSG_BOOT)
MSG_BOOT_COORD = (oled.width // 2 - msg_boot_width // 2, 20)

MSG_READY = "Ready"
MSG_READY_FONT = font
(msg_ready_width, _) = MSG_READY_FONT.getsize(MSG_READY)
MSG_READY_COORD = (oled.width // 2 - msg_ready_width // 2, 20)

MSG_ERR_CAM = "\u2620Cam"
MSG_ERR_CAM_FONT = font
MSG_ERR_CAM_COORD = (1, 16)

MSG_CONFIG = "\u270ECfg"
MSG_CONFIG_FONT = font
MSG_CONFIG_COORD = (1, 16)

MSG_DOUBT = "\u2049" # \u2718
MSG_DOUBT_FONT = font2
(msg_doubt_width, _) = font2.getsize(MSG_DOUBT)
MSG_DOUBT_COORD = (1, 0)

MSG_BREAK = "Pause"
MSG_BREAK_FONT = font2
# (msg_break_width, _) = MSG_BREAK_FONT.getsize(MSG_BREAK)
MSG_BREAK_COORD = (msg_doubt_width + 4, 0)

MSG_REMOVE_TILES = "Entf. Zug"
MSG_REMOVE_TILES_FONT = font2
# (msg_remove_width, _) = MSG_REMOVE_TILES_FONT.getsize(MSG_REMOVE_TILES)
MSG_REMOVE_TILES_COORD = (msg_doubt_width + 4, 1)

MSG_MALUS = "-10 Pkt"
MSG_MALUS_FONT = font2
# (msg_malus_width, _) = MSG_MALUS_FONT.getsize(MSG_MALUS)
MSG_MALUS_COORD = (msg_doubt_width + 4, 1)


# Boot message
print('Boot message')
image.paste(empty)
draw.text(MSG_BOOT_COORD, MSG_BOOT, font=MSG_BOOT_FONT, fill=255)
oled.image(image)
oled.show()
time.sleep(2)

# Ready message
print('Ready message')
image.paste(empty)
draw.text(MSG_READY_COORD, MSG_READY, font=MSG_READY_FONT, fill=255)
for i in range(0, 2):
    display(i)
    print(f'{i:d}: ready')
    oled.image(image)
    oled.show()
time.sleep(2)

display(0)
# Error message CAM
print('Err CAM')
image.paste(empty)
draw.text(MSG_ERR_CAM_COORD, MSG_ERR_CAM, font=MSG_ERR_CAM_FONT, fill=255)
oled.image(image)
oled.show()
time.sleep(2)

# Config message
print('Config')
image.paste(empty)
draw.text(MSG_CONFIG_COORD, MSG_CONFIG, font=MSG_CONFIG_FONT, fill=255)
oled.image(image)
oled.show()
time.sleep(2)

for i in range(0,2):
    display(i)
    print(f'{i:d}: reset timer display')
    m1, s1 = divmod(abs(1800), 60)
    image.paste(empty)
    text = '30:00'
    (font_width, _) = font.getsize(text)
    draw.text((oled.width // 2 - font_width // 2, 22), text, font=font, fill=255)
    t2 = '0'
    (font_width, _) = font2.getsize(t2)
    draw.text((oled.width - font_width, 0), t2, font=font2, fill=128)
    oled.image(image)
    oled.show()

display(0)
print('Countdown')
for i in range(0, 11):
    m1, s1 = divmod(abs(1800 - i), 60)
    image.paste(empty)
    text = f"{m1:02d}:{s1:02d}"
    (font_width, _) = font.getsize(text)
    draw.text((oled.width // 2 - font_width // 2, 22), text, font=font, fill=255)
    t2 = f"{i:4d}"
    (font_width, _) = font2.getsize(t2)
    draw.text((oled.width - font_width, 0), t2, font=font2, fill=128)
    if i <= 5:
        draw.text(MSG_DOUBT_COORD, MSG_DOUBT, font=MSG_DOUBT_FONT, fill=255)
    oled.image(image)
    oled.show()
    time.sleep(1)

print('Pause')
oled.invert(True)
draw.text(MSG_BREAK_COORD, MSG_BREAK, font=MSG_BREAK_FONT, fill=255)
oled.image(image)
oled.show()
time.sleep(2)

# Pause
# image.paste(empty)
# draw.text( MSG_BREAK_COORD, MSG_BREAK, font=MSG_BREAK_FONT, fill=255)
# draw.text( MSG_DOUBT_COORD, MSG_DOUBT, font=MSG_DOUBT_FONT, fill=255)
# m1, s1 = divmod(abs(1800 - 10), 60)
# text = f'{m1:02d}:{s1:02d}'
# (font_width, _) = font.getsize(text)
# draw.text((oled.width // 2 - font_width // 2, 22), text, font=font, fill=255)
# oled.image(image)
print('Pause mit Annotation')
draw.text(MSG_DOUBT_COORD, MSG_DOUBT, font=MSG_DOUBT_FONT, fill=255)
draw.text(MSG_BREAK_COORD, MSG_BREAK, font=MSG_BREAK_FONT, fill=255)
oled.image(image)
oled.show()
time.sleep(5)

display(1)

# Entferne Zug
print('Entf. Zug')
image.paste(empty)
draw.text(
    MSG_REMOVE_TILES_COORD, MSG_REMOVE_TILES, font=MSG_REMOVE_TILES_FONT, fill=255
)
draw.text(MSG_DOUBT_COORD, MSG_DOUBT, font=MSG_DOUBT_FONT, fill=255)
m1, s1 = divmod(abs(1800 - 10), 60)
text = f"{m1:02d}:{s1:02d}"
(font_width, font_height) = font.getsize(text)
draw.text((oled.width // 2 - font_width // 2, 22), text, font=font, fill=255)
oled.image(image)
oled.invert(True)
oled.show()
time.sleep(2)

# Strafpunkte
print('Malus')
image.paste(empty)
draw.text(MSG_MALUS_COORD, MSG_MALUS, font=MSG_MALUS_FONT, fill=255)
draw.text(MSG_DOUBT_COORD, MSG_DOUBT, font=MSG_DOUBT_FONT, fill=255)
m1, s1 = divmod(abs(1800 - 10), 60)
text = f"{m1:02d}:{s1:02d}"
(font_width, font_height) = font.getsize(text)
draw.text((oled.width // 2 - font_width // 2, 22), text, font=font, fill=255)
oled.image(image)
oled.invert(True)
oled.show()
time.sleep(2)


display(0)
print('0: switch off')
oled.invert(False)
oled.poweroff()
display(1)
print('1: switch off')
oled.invert(False)
oled.poweroff()

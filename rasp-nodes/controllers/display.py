from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import busio
from board import SCL, SDA

# ==========================
# Setup do display
# ==========================
i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

disp.fill(0)
disp.show()
width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
padding = -2
top = padding
x = 0

# ===============================
# Funções utilitárias do display
# ===============================
def display_message(line1="", line2="", line3="", line4="", line5="", clear=True):
    if clear:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    lines = [line1, line2, line3, line4, line5]
    for cont, line in enumerate(lines):
        if line:
            draw.text((x, top + (cont * 12)), line, font=font, fill=255)
    
    disp.image(image)
    disp.show()

def draw_network_info(info):
    display_message(
        f"Host: {info['HOST']}",
        f"IP: {info['IP']}",
        f"WIFI: {info['WIFI'][:18]}",
        f"SSH: {info['SSH']} Users:{info['USERS']}",
        f"SSID: {info['SSID'][:18]}"
    )

def draw_ssid_selection(ssids, current_index, scroll_offset=0):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((x, top), "Selecione SSID:", font=font, fill=255)
    
    visible_ssids = ssids[scroll_offset:scroll_offset + 4]
    
    for cont, ssid in enumerate(visible_ssids):
        actual_index = scroll_offset + cont
        if actual_index == current_index:
            prefix = ">"
        else:
            prefix = " "
        draw.text((x, top + 12 + (cont * 12)), f"{prefix}{ssid[:19]}", font=font, fill=255)
    
    disp.image(image)
    disp.show()

def draw_password_input(ssid, password, show_chars=False):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((x, top), f"SSID: {ssid[:15]}", font=font, fill=255)
    draw.text((x, top + 12), "Senha:", font=font, fill=255)
   
    if show_chars:
        display_pwd = password[-18:]
    else:
        display_pwd = "*" * min(len(password), 18)

    draw.text((x, top + 24), display_pwd, font=font, fill=255)
    draw.text((x, top + 48), "Enter=OK ESC=Cancel", font=font, fill=255)
    
    disp.image(image)
    disp.show()

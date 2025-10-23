from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import busio
from board import SCL, SDA

# Configuração do display
i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

disp.fill(0)
disp.show()
width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# Fontes
font_title = ImageFont.load_default()  # Pode trocar para uma fonte TTF usando ImageFont.truetype se desejar
font_normal = ImageFont.load_default()

def draw_centered_text(draw, text, y, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (width - w) // 2
    draw.text((x, y), text, font=font, fill=255)

def display_message(line1="", line2="", line3="", line4="", line5="", clear=True):
    if clear:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Título centralizado (linha 1)
    if line1:
        draw_centered_text(draw, line1, 0, font=font_title)

    # Linha separadora abaixo do título
    draw.line((0, 12, width, 12), fill=255)

    # Conteúdo alinhado à esquerda
    content_lines = [line2, line3, line4, line5]
    y_start = 16
    line_height = 12
    for idx, line in enumerate(content_lines):
        if line:
            draw.text((2, y_start + idx * line_height), line, font=font_normal, fill=255)

    disp.image(image)
    disp.show()

def draw_network_info(info):
    display_message(
        f"SSID: {info.get('SSID', 'Desconhecido')[:19]}",
        f"Host: {info.get('HOST', '')}",
        f"IP: {info.get('IP', '')}",
        f"WiFi: {info.get('WIFI', '')[:18]}",
        f"SSH: {info.get('SSH', '')} Users:{info.get('USERS', '')}"
    )

def draw_ssid_selection(ssids, current_index, scroll_offset=0):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    draw_centered_text(draw, "Selecione SSID", 0, font=font_title)
    draw.line((0, 12, width, 12), fill=255)

    visible_ssids = ssids[scroll_offset:scroll_offset + 4]
    box_height = 12
    y_start = 16

    for idx, ssid in enumerate(visible_ssids):
        y = y_start + idx * box_height
        if scroll_offset + idx == current_index:
            # Caixa de seleção invertida para destacar
            draw.rectangle((0, y - 1, width, y + box_height - 1), outline=255, fill=1)
            draw.text((4, y), ssid[:19], font=font_normal, fill=0)
        else:
            draw.text((4, y), ssid[:19], font=font_normal, fill=255)

    disp.image(image)
    disp.show()

def draw_password_input(ssid, password, show_chars=False):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    draw_centered_text(draw, "Conectar WiFi", 0, font=font_title)
    draw.line((0, 12, width, 12), fill=255)

    ssid_text = f"SSID: {ssid[:19]}"
    draw.text((2, 16), ssid_text, font=font_normal, fill=255)

    # Campo de senha com borda
    input_y = 32
    input_height = 12
    draw.rectangle((2, input_y - 2, width - 2, input_y + input_height + 2), outline=255, fill=0)

    if show_chars:
        display_pwd = password[-18:]
    else:
        display_pwd = "*" * min(len(password), 18)

    draw.text((4, input_y), display_pwd, font=font_normal, fill=255)

    draw.text((2, height - 12), "Enter=OK   ESC=Cancel", font=font_normal, fill=255)

    disp.image(image)
    disp.show()


from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import busio
from board import SCL, SDA

# ----------------------------------------------------------------------
# Cria a interface I2C, inicializa o display SSD1306 (128x64),
# ----------------------------------------------------------------------
i2c = busio.I2C(SCL, SDA)
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

disp.fill(0)
disp.show()
width = disp.width
height = disp.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

font_title = ImageFont.load_default()
font_normal = ImageFont.load_default()

def draw_centered_text(draw, text, y, font):
    """
    ----------------------------------------------------------------------
    @brief Desenha um texto centralizado horizontalmente.

    Calcula a largura do texto e posiciona-o no centro da tela, na altura Y indicada.

    @param draw: Objeto ImageDraw para desenhar.
    @param text: Texto a ser exibido.
    @param y: Posição vertical (em pixels).
    @param font: Fonte a ser usada.

    @return None
    ----------------------------------------------------------------------
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (width - w) // 2
    draw.text((x, y), text, font=font, fill=255)


def display_message(line1="", line2="", line3="", line4="", line5="", clear=True):
    """
    ----------------------------------------------------------------------
    @brief Exibe até 5 linhas de texto na tela, centralizando a primeira.

    A primeira linha é o título (centralizada), seguida por uma linha divisória,
    e até 4 linhas de conteúdo alinhadas à esquerda.

    @param line1: Texto da linha 1 (título).
    @param line2: Texto da linha 2.
    @param line3: Texto da linha 3.
    @param line4: Texto da linha 4.
    @param line5: Texto da linha 5.
    @param clear: Define se a tela deve ser limpa antes de desenhar (padrão True).

    @return None
    ----------------------------------------------------------------------
    """
    if clear:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

    if line1:
        draw_centered_text(draw, line1, 0, font=font_title)

    draw.line((0, 12, width, 12), fill=255)

    content_lines = [line2, line3, line4, line5]
    y_start = 16
    line_height = 12
    for idx, line in enumerate(content_lines):
        if line:
            draw.text((2, y_start + idx * line_height), line, font=font_normal, fill=255)

    disp.image(image)
    disp.show()


def draw_network_info(info):
    """
    ----------------------------------------------------------------------
    @brief Exibe informações de rede no display.

    Mostra SSID, host, IP, qualidade do Wi-Fi e número de usuários SSH.

    @param info: Dicionário contendo informações de rede. Chaves esperadas:
                 {'SSID', 'HOST', 'IP', 'WIFI', 'SSH', 'USERS'}

    @return None
    ----------------------------------------------------------------------
    """
    display_message(
        f"SSID: {info.get('SSID', 'Desconhecido')[:19]}",
        f"Host: {info.get('HOST', '')}",
        f"IP: {info.get('IP', '')}",
        f"WiFi: {info.get('WIFI', '')[:18]}",
        f"SSH: {info.get('SSH', '')} Users:{info.get('USERS', '')}"
    )


def draw_ssid_selection(ssids, current_index, scroll_offset=0):
    """
    ----------------------------------------------------------------------
    @brief Exibe lista de SSIDs disponíveis e destaca o SSID selecionado.

    Mostra até 4 SSIDs visíveis por vez e desenha uma caixa invertida
    em torno do SSID atualmente selecionado.

    @param ssids: Lista de strings com nomes de redes.
    @param current_index: Índice do SSID atualmente selecionado.
    @param scroll_offset: Índice de início da lista visível (para rolagem).

    @return None
    ----------------------------------------------------------------------
    """
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    draw_centered_text(draw, "Selecione SSID", 0, font=font_title)
    draw.line((0, 12, width, 12), fill=255)

    visible_ssids = ssids[scroll_offset:scroll_offset + 4]
    box_height = 12
    y_start = 16

    for idx, ssid in enumerate(visible_ssids):
        y = y_start + idx * box_height
        if scroll_offset + idx == current_index:
            draw.rectangle((0, y - 1, width, y + box_height - 1), outline=255, fill=1)
            draw.text((4, y), ssid[:19], font=font_normal, fill=0)
        else:
            draw.text((4, y), ssid[:19], font=font_normal, fill=255)

    disp.image(image)
    disp.show()


def draw_password_input(ssid, password, show_chars=False):
    """
    ----------------------------------------------------------------------
    @brief Exibe a tela de entrada de senha para conexão Wi-Fi.

    Mostra o SSID atual, um campo de senha (ocultando ou exibindo caracteres)
    e uma linha de ajuda indicando teclas de controle.

    @param ssid: Nome da rede Wi-Fi atual.
    @param password: String com a senha digitada até o momento.
    @param show_chars: Se True, exibe caracteres reais; senão, mostra asteriscos.

    @return None
    ----------------------------------------------------------------------
    """
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    draw_centered_text(draw, "Conectar WiFi", 0, font=font_title)
    draw.line((0, 12, width, 12), fill=255)

    ssid_text = f"SSID: {ssid[:19]}"
    draw.text((2, 16), ssid_text, font=font_normal, fill=255)

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


def draw_password_roulette(ssid, password, charset, cursor_pos):
    """
    ----------------------------------------------------------------------
    @brief Exibe a tela de entrada de senha no formato roleta de caracteres.

    Permite ao usuário digitar a senha para conexão Wi-Fi selecionando
    caracteres de um conjunto pré-definido, simulando uma "roleta" que
    pode ser navegado com botões físicos.

    Mostra o SSID atual, o campo de senha com caracteres ocultos,
    a faixa de caracteres vizinhos à posição do cursor, e indicação 
    visual do caractere atualmente selecionado.

    @param ssid: String do nome da rede Wi-Fi atual.
    @param password: String da senha digitada até o momento (simbolizada por asteriscos).
    @param charset: String ou lista de caracteres disponíveis para seleção.
    @param cursor_pos: Posição inteira atual na roleta de caracteres.

    @return None
    ----------------------------------------------------------------------
    """
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw_centered_text(draw, "Conectar WiFi", 0, font=font_title)
    draw.line((0, 12, width, 12), fill=255)

    draw.text((2, 16), f"SSID: {ssid[:19]}", font=font_normal, fill=255)
    display_pwd = "*" * len(password)
    draw.text((2, 28), f"Senha: {display_pwd}", font=font_normal, fill=255)

    # Exibe roleta de caracteres (posição atual centralizada)
    start = max(cursor_pos - 2, 0)
    end = min(cursor_pos + 3, len(charset))
    chars_visiveis = [charset[i] for i in range(start, end)]
    roleta = " ".join(chars_visiveis)
    draw.text((2, 44), roleta, font=font_normal, fill=255)
    setas_x = 2 + (cursor_pos - start) * 8
    draw.text((setas_x, 54), "^", font=font_normal, fill=255)

    disp.image(image)
    disp.show()


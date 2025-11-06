from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import busio
from board import SCL, SDA

# Inicializa display
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
    """Desenha texto centralizado horizontalmente."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (width - w) // 2
    draw.text((x, y), text, font=font, fill=255)


def display_message(line1="", line2="", line3="", line4="", line5="", clear=True):
    """Exibe mensagem multi-linha no display."""
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
    """Exibe informações de rede."""
    display_message(
        f"SSID: {info.get('SSID', 'Desconhecido')[:19]}",
        f"Host: {info.get('HOST', '')}",
        f"IP: {info.get('IP', '')}",
        f"WiFi: {info.get('WIFI', '')[:18]}",
        f"SSH: {info.get('SSH', '')} Users:{info.get('USERS', '')}"
    )


def draw_ssid_selection(ssids, current_index, scroll_offset=0):
    """Exibe lista de SSIDs com seleção visual."""
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


def draw_password_input(ssid, password, cursor_pos=0):
    """
    Interface moderna para entrada de senha.
    Mostra caracteres reais com cursor piscante.
    Usa toda a largura da tela (20 caracteres visíveis).
    """
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Cabeçalho
    draw_centered_text(draw, "WiFi Password", 0, font=font_title)
    draw.line((0, 11, width, 11), fill=255)
    
    # SSID truncado se necessário
    ssid_display = ssid[:20] if len(ssid) <= 20 else ssid[:17] + "..."
    draw.text((2, 14), f"{ssid_display}", font=font_normal, fill=255)
    
    # Área de senha com borda
    pwd_box_y = 28
    pwd_box_height = 15
    draw.rectangle((0, pwd_box_y, width, pwd_box_y + pwd_box_height), outline=255, fill=0)
    
    # Exibe senha (máximo 20 caracteres visíveis)
    if len(password) <= 20:
        pwd_display = password
        cursor_x = 2 + len(password) * 6
    else:
        # Rolagem: mostra últimos 20 caracteres
        pwd_display = password[-20:]
        cursor_x = 2 + 20 * 6
    
    draw.text((2, pwd_box_y + 3), pwd_display, font=font_normal, fill=255)
    
    # Cursor piscante (linha vertical)
    if cursor_x < width - 2:
        draw.line((cursor_x, pwd_box_y + 2, cursor_x, pwd_box_y + pwd_box_height - 2), fill=255)
    
    # Instruções na parte inferior
    draw.text((2, 46), "< >  Mudar   OK  Aceitar", font=font_normal, fill=255)
    draw.text((2, 56), "Backspace: Pressione OK", font=font_normal, fill=255)
    
    disp.image(image)
    disp.show()


def draw_password_roulette(ssid, password, charset, cursor_pos):
    """
    Interface de roleta para entrada de senha.
    Mostra caracteres reais e navegação mais intuitiva.
    """
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Cabeçalho compacto
    draw_centered_text(draw, "WiFi", 0, font=font_title)
    draw.line((0, 10, width, 10), fill=255)
    
    # SSID compacto
    ssid_display = ssid[:20] if len(ssid) <= 20 else ssid[:17] + "..."
    draw.text((2, 12), ssid_display, font=font_normal, fill=255)
    
    # Senha atual em caixa (mostra últimos 18 caracteres)
    if len(password) <= 18:
        pwd_display = password if password else "(vazio)"
    else:
        pwd_display = ".." + password[-16:]
    
    # Caixa da senha
    pwd_box_y = 24
    draw.rectangle((1, pwd_box_y, width - 1, pwd_box_y + 11), outline=255, fill=0)
    draw.text((3, pwd_box_y + 1), pwd_display, font=font_normal, fill=255)
    
    # Roleta de caracteres - mostra 7 caracteres
    chars_per_view = 7
    mid_point = chars_per_view // 2
    
    start_idx = max(0, cursor_pos - mid_point)
    end_idx = min(len(charset), start_idx + chars_per_view)
    
    if end_idx - start_idx < chars_per_view:
        start_idx = max(0, end_idx - chars_per_view)
    
    visible_chars = charset[start_idx:end_idx]
    
    # Desenha roleta mais compacta
    char_width = 16
    start_x = (width - (len(visible_chars) * char_width)) // 2
    
    for i, char in enumerate(visible_chars):
        char_idx = start_idx + i
        x_pos = start_x + (i * char_width)
        y_pos = 42
        
        if char_idx == cursor_pos:
            # Caractere selecionado
            draw.rectangle((x_pos - 2, y_pos - 1, x_pos + 10, y_pos + 11), 
                          outline=255, fill=255)
            draw.text((x_pos, y_pos), char, font=font_normal, fill=0)
            # Seta menor
            draw.text((x_pos + 3, y_pos + 12), "^", font=font_normal, fill=255)
        else:
            draw.text((x_pos, y_pos), char, font=font_normal, fill=255)
    
    # Dicas de uso na base
    try:
        draw.text((2, 56), "< back  >/=/# OK", font=font_normal, fill=255)
    except Exception:
        # Em caso de fonte sem suporte, ignorar
        pass

    disp.image(image)
    disp.show()
    

def draw_connecting(ssid):
    """Tela de conexão em progresso."""
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw_centered_text(draw, "Conectando...", 0, font=font_title)
    draw.line((0, 11, width, 11), fill=255)
    
    ssid_display = ssid[:20] if len(ssid) <= 20 else ssid[:17] + "..."
    draw_centered_text(draw, ssid_display, 28, font=font_normal)
    
    # Animação simples
    draw_centered_text(draw, "Aguarde...", 45, font=font_normal)
    
    disp.image(image)
    disp.show()


def draw_success(ssid, ip=""):
    """Tela de sucesso na conexão."""
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw_centered_text(draw, "Conectado!", 0, font=font_title)
    draw.line((0, 11, width, 11), fill=255)
    
    ssid_display = ssid[:20] if len(ssid) <= 20 else ssid[:17] + "..."
    draw.text((2, 18), ssid_display, font=font_normal, fill=255)
    
    if ip:
        draw.text((2, 32), f"IP: {ip}", font=font_normal, fill=255)
    
    draw_centered_text(draw, "OK para continuar", 50, font=font_normal)
    
    disp.image(image)
    disp.show()


def draw_error(message):
    """Tela de erro."""
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw_centered_text(draw, "Erro", 0, font=font_title)
    draw.line((0, 11, width, 11), fill=255)
    
    # Quebra mensagem em linhas
    words = message.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if len(test_line) <= 20:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Exibe até 3 linhas
    y = 20
    for line in lines[:3]:
        draw.text((2, y), line, font=font_normal, fill=255)
        y += 12
    
    draw_centered_text(draw, "OK para voltar", 52, font=font_normal)
    
    disp.image(image)
    disp.show()


def draw_logo():
    """Exibe a logo da apresentação."""
    try:
        from assets.logo_bitmap import logo_bitmap_bytes
        
        # Limpa a tela
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        
        # Tenta converter byte array para imagem
        # Formato SSD1306: cada byte representa 8 pixels verticais consecutivos
        # Para 128x64: são 128 colunas * 8 linhas por byte = 1024 bytes
        if len(logo_bitmap_bytes) == 1024:
            # Converte byte array para imagem PIL
            # Formato: para cada coluna x, bytes são organizados verticalmente
            # Cada byte representa 8 pixels verticais (LSB no topo)
            logo_img = Image.new("1", (128, 64))
            pixels = logo_img.load()
            
            for x in range(128):
                for y_page in range(8):  # 64 pixels / 8 = 8 páginas
                    byte_idx = x + (y_page * 128)
                    if byte_idx < len(logo_bitmap_bytes):
                        byte_val = logo_bitmap_bytes[byte_idx]
                        for bit in range(8):
                            y = y_page * 8 + bit
                            if y < 64:
                                if byte_val & (1 << bit):  # LSB primeiro
                                    pixels[x, y] = 1
                                else:
                                    pixels[x, y] = 0
            
            # Usa a imagem convertida
            image.paste(logo_img, (0, 0))
        
        # Se tem outro tamanho, tenta tratar como imagem PIL direto
        elif len(logo_bitmap_bytes) > 0:
            try:
                # Tenta carregar como imagem
                import io
                logo_img = Image.open(io.BytesIO(logo_bitmap_bytes))
                logo_img = logo_img.convert("1").resize((128, 64))
                
                # Centraliza
                x_offset = (width - logo_img.width) // 2
                y_offset = (height - logo_img.height) // 2
                image.paste(logo_img, (x_offset, y_offset))
            except Exception:
                # Se falhar, exibe texto alternativo
                draw_centered_text(draw, "RASPBERRY", 20, font=font_title)
                draw_centered_text(draw, "GATE", 35, font=font_title)
        else:
            # Byte array vazio, exibe texto alternativo
            draw_centered_text(draw, "RASPBERRY", 20, font=font_title)
            draw_centered_text(draw, "GATE", 35, font=font_title)
        
        disp.image(image)
        disp.show()
        
    except ImportError:
        # Se não conseguir importar, exibe texto alternativo
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw_centered_text(draw, "RASPBERRY", 20, font=font_title)
        draw_centered_text(draw, "GATE", 35, font=font_title)
        disp.image(image)
        disp.show()
    except Exception as e:
        # Em caso de erro, exibe texto alternativo
        print(f"Erro ao exibir logo: {e}")
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw_centered_text(draw, "RASPBERRY", 20, font=font_title)
        draw_centered_text(draw, "GATE", 35, font=font_title)
        disp.image(image)
        disp.show()


def draw_students_names():
    """Exibe os nomes dos alunos na apresentação."""
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Título
    draw_centered_text(draw, "Desenvolvido por", 5, font=font_normal)
    
    # Nomes dos alunos centralizados
    draw_centered_text(draw, "Miguel Ryan", 25, font=font_title)
    draw_centered_text(draw, "e", 38, font=font_normal)
    draw_centered_text(draw, "Guilherme Santos", 50, font=font_title)
    
    disp.image(image)
    disp.show()

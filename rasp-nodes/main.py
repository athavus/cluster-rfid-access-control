import subprocess
import time
import threading
from libs.keyboard import start_keyboard
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# ==========================
# Configuração do display
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

# ==========================
# Funções auxiliares
# ==========================
def get_connected_ssid():
    """Retorna o SSID conectado ou '' se nenhum."""
    try:
        cmd = "nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d: -f2"
        ssid = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return ssid
    except subprocess.CalledProcessError:
        return ""

def list_available_ssids():
    """Lista SSIDs disponíveis"""
    try:
        cmd = "nmcli -t -f ssid dev wifi | sort -u"
        available_ssids = subprocess.check_output(cmd, shell=True).decode("utf-8").splitlines()
        valid_ssids = [] 
        for ssid in available_ssids:
            if ssid:
                valid_ssids.append(ssid)
        return valid_ssids
    except subprocess.CalledProcessError:
        return []

def connect_to_wifi(ssid, password):
    """Tenta conectar à rede Wi-Fi"""
    try:
        cmd = f"nmcli dev wifi connect '{ssid}' password '{password}'"
        subprocess.check_output(cmd, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_network_info():
    """Retorna dicionário com informações da rede e SSH"""
    info = {}
    cmd = "hostname"
    info['HOST'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    cmd = "hostname -I | cut -d' ' -f1"
    info['IP'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    
    try:
        cmd = "iw dev wlan0 link | awk '/signal/ {sig=$2} /tx bitrate/ {rate=$3; printf \"%s dBm %s Mbit/s\", sig, rate}'"
        wifi_status = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        wifi_status = "desconectado"
    
    info['WIFI'] = wifi_status
    cmd = "systemctl is-active ssh"
    info['SSH'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    cmd = "w -h | wc -l"
    info['USERS'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    info['SSID'] = get_connected_ssid()
    return info

def display_message(line1="", line2="", line3="", line4="", line5="", clear=True):
    """Função genérica para exibir mensagens no display"""
    if clear:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    lines = [line1, line2, line3, line4, line5]
    for cont, line in enumerate(lines):
        if line:
            draw.text((x, top + (cont * 12)), line, font=font, fill=255)
    
    disp.image(image)
    disp.show()

def draw_network_info(info):
    """Desenha informações de rede no display OLED"""
    display_message(
        f"Host: {info['HOST']}",
        f"IP: {info['IP']}",
        f"WIFI: {info['WIFI'][:18]}",  # Trunca para caber na tela
        f"SSH: {info['SSH']} Users:{info['USERS']}",
        f"SSID: {info['SSID'][:18]}"
    )

def draw_ssid_selection(ssids, current_index, scroll_offset=0):
    """Desenha menu de seleção de SSID com rolagem"""
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((x, top), "Selecione SSID:", font=font, fill=255)
    
    # Mostra até 4 SSIDs por vez
    visible_ssids = ssids[scroll_offset:scroll_offset + 4]
    
    for cont, ssid in enumerate(visible_ssids):
        actual_index = scroll_offset + cont
        if actual_index == current_index:
            prefix = ">"
        else:
            prefix = " "

        ssid_truncated = ssid[:19]
        draw.text((x, top + 12 + (cont * 12)), f"{prefix}{ssid_truncated}", font=font, fill=255)
    
    disp.image(image)
    disp.show()

def draw_password_input(ssid, password, show_chars=False):
    """Desenha tela de entrada de senha"""
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((x, top), f"SSID: {ssid[:15]}", font=font, fill=255)
    draw.text((x, top + 12), "Senha:", font=font, fill=255)
    
    # Mostra caracteres ou asteriscos
    if show_chars:
        if len(password) > 18:
            display_pwd = password[-18:]
        else: 
            display_pwd = password
    else:
        display_pwd = "*" * min(len(password), 18)
    
    draw.text((x, top + 24), display_pwd, font=font, fill=255)
    draw.text((x, top + 48), "Enter=OK ESC=Cancel", font=font, fill=255)
    
    disp.image(image)
    disp.show()

# ==========================
# Inicializa teclado
# ==========================
kb = start_keyboard("/dev/input/event1")
kb.clear_buffer()

# Thread para teclado
def teclado_thread():
    kb.listen(lambda char: None)  # Apenas mantém o listener ativo

t = threading.Thread(target=teclado_thread, daemon=True)
t.start()

# ==========================
# Loop principal
# ==========================
try:
    # Mensagem de inicialização
    display_message("", "Inicializando...", "", "Sistema WiFi v1.0", "")
    time.sleep(2)
    
    while True:
        ssid = get_connected_ssid()
        
        if ssid:
            # Caso conectado: mostra info da rede
            info = get_network_info()
            draw_network_info(info)
            time.sleep(1)
        else:
            # Caso desconectado: busca redes disponíveis
            display_message("", "Buscando redes...", "", "Aguarde...", "")
            time.sleep(1)
            
            available_ssids = list_available_ssids()
            
            if not available_ssids:
                display_message("", "Nenhuma rede", "encontrada!", "", "Tentando novamente...")
                time.sleep(3)
                continue
            
            # Menu de seleção de SSID
            index = 0
            scroll_offset = 0
            selecting_ssid = True
            
            while selecting_ssid:
                # Ajusta scroll para manter item selecionado visível
                if index < scroll_offset:
                    scroll_offset = index
                elif index >= scroll_offset + 4:
                    scroll_offset = index - 3
                
                draw_ssid_selection(available_ssids, index, scroll_offset)
                time.sleep(0.1)
                
                buf = kb.get_buffer()

                if buf.endswith("\x1b[A"):  # Seta cima
                    index = (index - 1) % len(available_ssids)
                    kb.clear_buffer()                    
                elif buf.endswith("\x1b[B"):  # Seta baixo
                    index = (index + 1) % len(available_ssids)
                    kb.clear_buffer()
                elif buf.endswith("\x1b"):  # ESC - atualizar lista
                    kb.clear_buffer()
                    display_message("", "Atualizando lista...", "", "Aguarde...", "")
                    time.sleep(1)
                    break
                elif buf.endswith("\r"):  # Enter
                    selected_ssid = available_ssids[index]
                    kb.clear_buffer()
                    
                    # Entrada de senha
                    password = ""
                    entering_password = True
                    
                    while entering_password:
                        draw_password_input(selected_ssid, password)
                        time.sleep(0.1)
                        
                        current_buffer = kb.get_buffer()
                        
                        if current_buffer.endswith("\r"):  # Enter - tentar conectar
                            password = current_buffer.rstrip("\r\n")
                            kb.clear_buffer()
                            
                            display_message("", "Conectando...", "", f"SSID: {selected_ssid[:15]}", "Aguarde...")
                            
                            success = connect_to_wifi(selected_ssid, password)
                            
                            if success:
                                display_message("", "Conectado!", "", f"SSID: {selected_ssid[:15]}", "")
                                time.sleep(2)
                            else:
                                display_message("", "Falha na conexao!", "", "Senha incorreta?", "Tente novamente...")
                                time.sleep(3)
                            
                            entering_password = False
                            selecting_ssid = False
                            
                        elif current_buffer.endswith("\x1b"):  # ESC - cancelar
                            kb.clear_buffer()
                            display_message("", "Cancelado!", "", "Voltando ao menu...", "")
                            time.sleep(1)
                            entering_password = False
                        else:
                            password = current_buffer

except KeyboardInterrupt:
    display_message("", "", "Sistema", "Finalizado", "")
    time.sleep(2)
    disp.fill(0)
    disp.show()

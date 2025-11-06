import time
from controllers.display import draw_network_info
from controllers.buttons import read_button
from controllers.wifi import list_available_ssids, get_network_info
from system.modes.ssid_selection import handle_ssid_selection

def handle_connected_mode():
    info = get_network_info()
    draw_network_info(info)
    time.sleep(0.1)

    btn = read_button()
    if btn == 'ok':
        available_ssids = list_available_ssids()
        handle_ssid_selection(available_ssids)

def run_system():
    try:
        from controllers.display import display_message, disp, draw_logo, draw_students_names
        
        # Apresentação inicial
        # Exibe logo por 3.5 segundos
        draw_logo()
        time.sleep(3.5)
        
        # Exibe nomes dos alunos por 2 segundos
        draw_students_names()
        time.sleep(2)
        
        # Continua com inicialização normal
        display_message("", "Inicializando...", "Sistema", "", "")
        time.sleep(1)

        while True:
            from controllers.wifi import get_connected_ssid
            ssid = get_connected_ssid()

            if ssid:
                handle_connected_mode()
            else:
                from system.modes.disconnected import handle_disconnected_mode
                handle_disconnected_mode()

    except KeyboardInterrupt:
        display_message("", "", "Sistema", "Finalizado", "")
        time.sleep(1)
        disp.fill(0)
        disp.show()
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except ImportError:
            pass  # GPIO não disponível


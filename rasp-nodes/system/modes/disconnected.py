import time
from controllers.display import draw_ssid_selection, display_message
from controllers.buttons import read_button
from system.modes.password_input import handle_password_input
from controllers.wifi import list_available_ssids

def handle_disconnected_mode():
    display_message("", "Buscando redes...", "", "Aguarde...", "")
    time.sleep(1)
    available_ssids = list_available_ssids()

    if not available_ssids:
        display_message("", "Nenhuma rede", "encontrada!", "", "Tentando novamente...")
        time.sleep(1)
        return

    handle_ssid_selection(available_ssids)


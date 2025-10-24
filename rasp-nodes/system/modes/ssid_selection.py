import time
from controllers.display import draw_ssid_selection, display_message
from controllers.keyboard import get_buffer, clear_buffer
from system.modes.password_input import handle_password_input

def handle_ssid_selection(available_ssids):
    """
    ----------------------------------------------------------------------
    @brief Gerencia a seleção de uma rede Wi-Fi disponível.

    Exibe uma lista de SSIDs disponíveis, permite navegação com
    setas do teclado e seleção de rede via Enter.
    ESC cancela a seleção ou atualiza a lista.

    Quando um SSID é selecionado, delega para handle_password_input
    para captura de senha.

    @param available_ssids: Lista de strings com os SSIDs disponíveis.

    @return None
    ----------------------------------------------------------------------
    """
    index, scroll_offset = 0, 0
    selecting_ssid = True

    while selecting_ssid:
        if index < scroll_offset:
            scroll_offset = index
        elif index >= scroll_offset + 4:
            scroll_offset = index - 3

        draw_ssid_selection(available_ssids, index, scroll_offset)
        time.sleep(0.1)
        buf = get_buffer()

        if buf.endswith("\x1b[A"):
            index = (index - 1) % len(available_ssids)
            clear_buffer()
        elif buf.endswith("\x1b[B"):
            index = (index + 1) % len(available_ssids)
            clear_buffer()
        elif buf.endswith("\x1b"):
            clear_buffer()
            display_message("", "Atualizando lista...", "Aguarde...", "", "")
            selecting_ssid = False
        elif buf.endswith("\r"):
            selected_ssid = available_ssids[index]
            clear_buffer()
            handle_password_input(selected_ssid)
            selecting_ssid = False

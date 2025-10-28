import time
from controllers.display import draw_network_info
from controllers.buttons import read_button
from controllers.wifi import list_available_ssids, get_network_info
from system.modes.ssid_selection import handle_ssid_selection

def handle_connected_mode():
    """
    ----------------------------------------------------------------------
    @brief Trata o modo de operação quando há conexão Wi-Fi ativa.

    Exibe informações da rede conectada e escuta botões.
    Se o usuário pressionar o botão OK, inicia o processo de seleção
    de outra rede Wi-Fi.

    @return None
    ----------------------------------------------------------------------
    """
    info = get_network_info()
    draw_network_info(info)
    time.sleep(0.1)

    btn = read_button()
    if btn == 'ok':  # botão OK → entra no modo de seleção de rede
        available_ssids = list_available_ssids()
        handle_ssid_selection(available_ssids)


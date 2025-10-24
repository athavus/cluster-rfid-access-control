import time
from controllers.display import display_message
from controllers.wifi import list_available_ssids
from system.modes.ssid_selection import handle_ssid_selection

def handle_disconnected_mode():
    """
    ----------------------------------------------------------------------
    @brief Trata o modo de operação quando não há conexão Wi-Fi.

    Exibe mensagem de busca de redes, aguarda um instante e tenta listar
    SSIDs disponíveis. Se houver redes disponíveis, delega para o
    modo de seleção de SSID. Se não houver, exibe mensagem e aguarda
    nova tentativa.

    @return None
    ----------------------------------------------------------------------
    """
    display_message("", "Buscando redes...", "", "Aguarde...", "")
    time.sleep(1)
    available_ssids = list_available_ssids()

    if not available_ssids:
        display_message("", "Nenhuma rede", "encontrada!", "", "Tentando novamente...")
        time.sleep(1)
        return

    handle_ssid_selection(available_ssids)

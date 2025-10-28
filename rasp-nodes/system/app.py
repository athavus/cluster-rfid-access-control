import time
from controllers.display import display_message
from controllers.wifi import get_connected_ssid
from system.modes.connected import handle_connected_mode
from system.modes.disconnected import handle_disconnected_mode

def run_system():
    """
    ----------------------------------------------------------------------
    @brief Loop principal do sistema.

    Inicializa a interface, entra em loop contínuo e delega o
    comportamento para modos conectados ou desconectados, dependendo
    do estado da conexão Wi-Fi.

    Trata interrupção pelo usuário (Ctrl+C) limpando o display.

    @return None
    ----------------------------------------------------------------------
    """
    try:
        display_message("", "Inicializando...", "Sistema", "", "")
        time.sleep(1)

        while True:
            ssid = get_connected_ssid()

            if ssid:
                handle_connected_mode()
            else:
                handle_disconnected_mode()

    except KeyboardInterrupt:
        display_message("", "", "Sistema", "Finalizado", "")
        time.sleep(1)
        from controllers.display import disp
        disp.fill(0)
        disp.show()


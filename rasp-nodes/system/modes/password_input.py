import time
from controllers.display import draw_password_input, display_message
from controllers.keyboard import get_buffer, clear_buffer
from controllers.wifi import connect_to_wifi

def handle_password_input(selected_ssid):
    """
    ----------------------------------------------------------------------
    @brief Gerencia a entrada de senha para conexão Wi-Fi.

    Exibe a tela de senha para o SSID selecionado, captura caracteres
    digitados, trata Enter (para conectar) e ESC (para cancelar).
    Atualiza o display conforme o estado da entrada e conexão.

    @param selected_ssid: Nome da rede Wi-Fi selecionada para conectar.

    @return None
    ----------------------------------------------------------------------
    """
    password = ""
    entering_password = True

    while entering_password:
        draw_password_input(selected_ssid, password)
        time.sleep(0.1)
        current_buffer = get_buffer()

        if current_buffer.endswith("\r"):
            password = current_buffer.rstrip("\r\n")
            clear_buffer()
            display_message("", "Conectando...", "", f"SSID: {selected_ssid[:19]}", "Aguarde...")
            success = connect_to_wifi(selected_ssid, password)
            display_message(
                "",
                "Conectado!" if success else "Falha na conexao!",
                "",
                f"SSID: {selected_ssid[:19]}",
                "" if success else "Tente novamente..."
            )
            entering_password = False
        elif current_buffer.endswith("\x1b"):
            clear_buffer()
            display_message("", "Cancelado!", "", "Voltando ao menu...", "")
            entering_password = False
        else:
            password = current_buffer

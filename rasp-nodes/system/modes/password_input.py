import time
from controllers.display import draw_password_roulette, display_message
from controllers.buttons import read_button
from controllers.wifi import connect_to_wifi

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 !@#$%&*()-_=+,. ><"

def handle_password_input(selected_ssid):
    """
    ----------------------------------------------------------------------
    @brief Gerencia a entrada de senha usando roleta de caracteres
           com botões físicos para conexão Wi-Fi.

    O usuário navega pelo conjunto de caracteres disponível (letras, números,
    símbolos) com botões de esquerda/direita, adicionando o caractere atual à senha
    usando o botão OK. O caractere especial '>' finaliza/confirmar o envio,
    e '<' apaga o último caractere digitado.

    Exibe constantemente o SSID em uso, senha parcial e roleta centralizada
    no display, até o usuário completar ou cancelar a operação.

    @param selected_ssid: String do SSID da rede escolhida.

    @return None
    ----------------------------------------------------------------------
    """
    password = ""
    cursor_pos = 0
    entering_password = True

    while entering_password:
        draw_password_roulette(selected_ssid, password, CHARSET, cursor_pos)
        btn = read_button()

        if btn == 'left':
            cursor_pos = (cursor_pos - 1) % len(CHARSET)
        elif btn == 'right':
            cursor_pos = (cursor_pos + 1) % len(CHARSET)
        elif btn == 'ok':
            char = CHARSET[cursor_pos]
            if char == '>':
                success = connect_to_wifi(selected_ssid, password)
                display_message("",
                                "Conectado!" if success else "Falha na conexao!",
                                "",
                                f"SSID: {selected_ssid[:19]}",
                                "" if success else "Tente novamente...")
                time.sleep(1)
                entering_password = False
            elif char == '<':
                password = password[:-1]
            else:
                password += char


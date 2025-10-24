import time
from controllers.display import display_message, draw_network_info, draw_ssid_selection, draw_password_input
from controllers.wifi import get_connected_ssid, list_available_ssids, connect_to_wifi, get_network_info
from controllers.keyboard import start_keyboard_listener, get_buffer, clear_buffer

# ----------------------------------------------------------------------
# Inicia o listener de teclado em thread separada.
# Permite capturar eventos de tecla de forma assíncrona em qualquer parte do loop.
# ----------------------------------------------------------------------
start_keyboard_listener()

try:
    # Exibe mensagem inicial na tela OLED
    display_message("", "Inicializando...", "", "Sistema", "")
    time.sleep(1)

    # ------------------------------------------------------------------
    # Loop principal do sistema
    # Mantém a interface interativa para exibir status da rede e gerenciar conexões.
    # ------------------------------------------------------------------
    while True:
        ssid = get_connected_ssid()  # Obtém SSID da rede atual, se houver

        if ssid:
            # ----------------------------------------------------------
            # Caso já esteja conectado a uma rede Wi-Fi:
            # Mostra as informações atuais da rede e escuta o teclado.
            # ----------------------------------------------------------
            info = get_network_info()
            draw_network_info(info)
            time.sleep(0.1)

            buf = get_buffer()
            if buf.endswith("\x1b"):  # ESC → entra no modo de seleção de rede
                clear_buffer()
                selecting_ssid = True
                available_ssids = list_available_ssids()
                index, scroll_offset = 0, 0

                # ------------------------------------------------------
                # Loop de seleção de SSID (usuário navega pelas redes disponíveis)
                # ------------------------------------------------------
                while selecting_ssid:
                    # Mantém a rolagem da lista dentro dos limites visíveis
                    if index < scroll_offset:
                        scroll_offset = index
                    elif index >= scroll_offset + 4:
                        scroll_offset = index - 3

                    draw_ssid_selection(available_ssids, index, scroll_offset)
                    time.sleep(0.1)
                    buf = get_buffer()

                    # Navegação entre SSIDs
                    if buf.endswith("\x1b[A"):  # Seta ↑
                        index = (index - 1) % len(available_ssids)
                        clear_buffer()
                    elif buf.endswith("\x1b[B"):  # Seta ↓
                        index = (index + 1) % len(available_ssids)
                        clear_buffer()
                    elif buf.endswith("\x1b"):  # ESC → sair da seleção
                        clear_buffer()
                        selecting_ssid = False
                    elif buf.endswith("\r"):  # ENTER → conectar
                        selected_ssid = available_ssids[index]
                        clear_buffer()
                        password = ""
                        entering_password = True

                        # ----------------------------------------------
                        # Loop de entrada de senha
                        # Permite digitar e confirmar com ENTER
                        # ----------------------------------------------
                        while entering_password:
                            draw_password_input(selected_ssid, password)
                            time.sleep(0.1)
                            current_buffer = get_buffer()

                            if current_buffer.endswith("\r"):
                                # ENTER → tenta conectar
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
                                selecting_ssid = False
                            elif current_buffer.endswith("\x1b"):  # ESC → cancelar entrada
                                clear_buffer()
                                display_message("", "Cancelado!", "", "Voltando ao menu...", "")
                                entering_password = False
                            else:
                                # Atualiza a senha conforme digita
                                password = current_buffer

        else:
            # ----------------------------------------------------------
            # Caso não haja rede conectada:
            # Mostra mensagem e busca novas redes disponíveis.
            # ----------------------------------------------------------
            display_message("", "Buscando redes...", "", "Aguarde...", "")
            time.sleep(1)
            available_ssids = list_available_ssids()

            if not available_ssids:
                display_message("", "Nenhuma rede", "encontrada!", "", "Tentando novamente...")
                time.sleep(1)
                continue

            # Inicia menu de seleção de SSID
            index, scroll_offset = 0, 0
            selecting_ssid = True

            while selecting_ssid:
                # Ajusta a rolagem da lista
                if index < scroll_offset:
                    scroll_offset = index
                elif index >= scroll_offset + 4:
                    scroll_offset = index - 3

                draw_ssid_selection(available_ssids, index, scroll_offset)
                time.sleep(0.1)
                buf = get_buffer()

                # Navegação entre redes
                if buf.endswith("\x1b[A"):
                    index = (index - 1) % len(available_ssids)
                    clear_buffer()
                elif buf.endswith("\x1b[B"):
                    index = (index + 1) % len(available_ssids)
                    clear_buffer()
                elif buf.endswith("\x1b"):
                    # ESC → Atualiza lista de redes
                    clear_buffer()
                    display_message("", "Atualizando lista...", "", "Aguarde...", "") 
                    break
                elif buf.endswith("\r"):
                    # ENTER → seleciona SSID e pede senha
                    selected_ssid = available_ssids[index]
                    clear_buffer()
                    password = ""
                    entering_password = True

                    while entering_password:
                        draw_password_input(selected_ssid, password)
                        time.sleep(0.1)
                        current_buffer = get_buffer()

                        if current_buffer.endswith("\r"):
                            # Tenta conectar com a senha digitada
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
                            selecting_ssid = False
                        elif current_buffer.endswith("\x1b"):
                            # ESC → cancelar conexão
                            clear_buffer()
                            display_message("", "Cancelado!", "", "Voltando ao menu...", "")
                            entering_password = False
                        else:
                            password = current_buffer

except KeyboardInterrupt:
    display_message("", "", "Sistema", "Finalizado", "")
    time.sleep(1)
    from controllers.display import disp
    disp.fill(0)
    disp.show()

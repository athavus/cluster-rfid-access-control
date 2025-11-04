import time
from controllers.display import draw_ssid_selection, display_message, draw_connecting, draw_success, draw_error
from controllers.buttons import read_button
from system.modes.password_input import handle_password_input
from controllers.wifi import known_connections, connect_to_wifi, list_available_ssids

def handle_ssid_selection(available_ssids):
    index, scroll_offset = 0, 0
    selecting_ssid = True
    last_scan_time = time.time()

    while selecting_ssid:
        # Atualiza lista de SSIDs a cada 8 segundos
        now = time.time()
        if now - last_scan_time >= 8:
            last_scan_time = now
            current_selected = available_ssids[index] if available_ssids else None
            new_list = list_available_ssids()
            if new_list:
                available_ssids = new_list
                if current_selected in available_ssids:
                    index = available_ssids.index(current_selected)
                else:
                    index = min(index, len(available_ssids) - 1)
                    if index < 0:
                        index = 0
                if index < scroll_offset:
                    scroll_offset = index
                elif index >= scroll_offset + 4:
                    scroll_offset = max(0, index - 3)
        if index < scroll_offset:
            scroll_offset = index
        elif index >= scroll_offset + 4:
            scroll_offset = index - 3

        draw_ssid_selection(available_ssids, index, scroll_offset)
        btn = read_button()

        if btn == 'left':
            index = (index - 1) % len(available_ssids)
        elif btn == 'right':
            index = (index + 1) % len(available_ssids)
        elif btn == 'ok':
            selected_ssid = available_ssids[index]
            print(f"\n[SSID Selection] SSID selecionado: '{selected_ssid}'")

            # Se rede já é conhecida, tenta conectar direto (pula senha)
            known_conns = known_connections()
            print(f"[SSID Selection] Conexões conhecidas: {known_conns}")
            
            if selected_ssid in known_conns:
                print(f"[SSID Selection] Rede '{selected_ssid}' é conhecida, conectando sem senha...")
                draw_connecting(selected_ssid)
                success = connect_to_wifi(selected_ssid, "")
                print(f"[SSID Selection] Resultado da conexão (rede conhecida): {success}")
                if success:
                    # Mostra sucesso (IP será mostrado pela próxima tela de status)
                    print(f"[SSID Selection] ✓ Conexão bem-sucedida!")
                    draw_success(selected_ssid)
                else:
                    print(f"[SSID Selection] ✗ Falha na conexão")
                    draw_error("Falha ao conectar")
                time.sleep(2)
                selecting_ssid = False
                continue

            # Caso contrário, pede senha e conecta
            print(f"[SSID Selection] Rede '{selected_ssid}' não é conhecida, solicitando senha...")
            def on_connect(ssid, password):
                print(f"\n[SSID Selection] Callback on_connect chamado!")
                print(f"[SSID Selection] SSID: '{ssid}'")
                print(f"[SSID Selection] Senha recebida: {'Sim (***)' if password else 'Não'}")
                print(f"[SSID Selection] Chamando connect_to_wifi...")
                
                ok = connect_to_wifi(ssid, password)
                
                print(f"[SSID Selection] Resultado de connect_to_wifi: {ok}")
                
                if ok:
                    # Retorna (success, message) sendo message o IP buscável na tela seguinte
                    print(f"[SSID Selection] ✓ Retornando sucesso ao password_input")
                    return (True, "")
                else:
                    # Mensagem de erro mais específica
                    # Se a rede tem senha mas a conexão falhou, pode ser senha incorreta ou timeout
                    print(f"[SSID Selection] ✗ Retornando erro ao password_input")
                    return (False, "Senha incorreta ou rede indisponivel")

            print(f"[SSID Selection] Iniciando handle_password_input...")
            handle_password_input(selected_ssid, on_connect_callback=on_connect)
            print(f"[SSID Selection] handle_password_input retornou")
            selecting_ssid = False


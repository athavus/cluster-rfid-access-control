import time
from controllers.display import display_message, draw_network_info, draw_ssid_selection, draw_password_input
from controllers.wifi import get_connected_ssid, list_available_ssids, connect_to_wifi, get_network_info
from controllers.keyboard import start_keyboard_listener, get_buffer, clear_buffer

start_keyboard_listener()

try:
    display_message("", "Inicializando...", "", "Sistema WiFi v1.0", "")
    time.sleep(2)
    
    while True:
        ssid = get_connected_ssid()
        
        if ssid:
            info = get_network_info()
            draw_network_info(info)
            time.sleep(1)
        else:
            display_message("", "Buscando redes...", "", "Aguarde...", "")
            time.sleep(1)
            available_ssids = list_available_ssids()
            
            if not available_ssids:
                display_message("", "Nenhuma rede", "encontrada!", "", "Tentando novamente...")
                time.sleep(3)
                continue
            
            index = 0
            scroll_offset = 0
            selecting_ssid = True
            
            while selecting_ssid:
                if index < scroll_offset:
                    scroll_offset = index
                elif index >= scroll_offset + 4:
                    scroll_offset = index - 3
                
                draw_ssid_selection(available_ssids, index, scroll_offset)
                time.sleep(0.1)
                
                buf = get_buffer()
                if buf.endswith("\x1b[A"):  # cima
                    index = (index - 1) % len(available_ssids)
                    clear_buffer()
                elif buf.endswith("\x1b[B"):  # baixo
                    index = (index + 1) % len(available_ssids)
                    clear_buffer()
                elif buf.endswith("\x1b"):  # ESC
                    clear_buffer()
                    display_message("", "Atualizando lista...", "", "Aguarde...", "")
                    time.sleep(1)
                    break
                elif buf.endswith("\r"):  # Enter
                    selected_ssid = available_ssids[index]
                    clear_buffer()
                    
                    password = ""
                    entering_password = True
                    
                    while entering_password:
                        draw_password_input(selected_ssid, password)
                        time.sleep(0.1)
                        current_buffer = get_buffer()
                        
                        if current_buffer.endswith("\r"):
                            password = current_buffer.rstrip("\r\n")
                            clear_buffer()
                            display_message("", "Conectando...", "", f"SSID: {selected_ssid[:15]}", "Aguarde...")
                            success = connect_to_wifi(selected_ssid, password)
                            display_message("", "Conectado!" if success else "Falha na conexao!",
                                            "", f"SSID: {selected_ssid[:15]}", "" if success else "Tente novamente...")
                            time.sleep(2)
                            entering_password = False
                            selecting_ssid = False
                        elif current_buffer.endswith("\x1b"):
                            clear_buffer()
                            display_message("", "Cancelado!", "", "Voltando ao menu...", "")
                            time.sleep(1)
                            entering_password = False
                        else:
                            password = current_buffer

except KeyboardInterrupt:
    display_message("", "", "Sistema", "Finalizado", "")
    time.sleep(2)
    from controllers.display import disp
    disp.fill(0)
    disp.show()

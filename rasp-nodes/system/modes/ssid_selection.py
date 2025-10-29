import time
from controllers.display import draw_ssid_selection, display_message
from controllers.buttons import read_button
from system.modes.password_input import handle_password_input

def handle_ssid_selection(available_ssids):
    index, scroll_offset = 0, 0
    selecting_ssid = True

    while selecting_ssid:
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
            handle_password_input(selected_ssid)
            selecting_ssid = False


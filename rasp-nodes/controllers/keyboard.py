import threading
from libs.keyboard import start_keyboard

kb = start_keyboard("/dev/input/event1")
kb.clear_buffer()

def teclado_thread():
    kb.listen(lambda char: None)

def start_keyboard_listener():
    t = threading.Thread(target=teclado_thread, daemon=True)
    t.start()

def get_buffer():
    return kb.get_buffer()

def clear_buffer():
    kb.clear_buffer()

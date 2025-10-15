# main.py
from libs.keyboard import start_keyboard
import time

# Inicia o teclado no device correto
kb = start_keyboard('/dev/input/event1')

while True:
    # Lê o buffer atual
    buf = kb.get_buffer()
    print("\rDigitado:", buf, end="", flush=True)
    time.sleep(0.5)


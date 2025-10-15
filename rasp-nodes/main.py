from evdev import InputDevice, categorize, ecodes
import threading

def read_keyboard():
    dev = InputDevice('/dev/input/event0');
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == key.key_down:
                print(f"Tecla pressionada: {key.keycode}")


t = threading.Thread(target=read_keyboard, daemon=True)
t.start()



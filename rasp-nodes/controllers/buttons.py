import RPi.GPIO as GPIO
import time

BUTTON_GPIO = {'left': 23, 'right': 27, 'ok': 22}
GPIO.setmode(GPIO.BCM)

for pin in BUTTON_GPIO.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Controle de debounce mais robusto
last_press_time = {'left': 0, 'right': 0, 'ok': 0}
DEBOUNCE_TIME = 0.2  # 200ms entre pressionamentos

def read_button():
    """
    Lê o estado dos botões com debounce aprimorado.
    Retorna o nome do botão pressionado ou None.
    """
    current_time = time.time()
    
    for name, pin in BUTTON_GPIO.items():
        if GPIO.input(pin) == GPIO.LOW:
            # Verifica se já passou tempo suficiente desde o último pressionamento
            if current_time - last_press_time[name] > DEBOUNCE_TIME:
                last_press_time[name] = current_time
                
                # Aguarda o botão ser solto
                timeout = time.time() + 1.0  # timeout de 1 segundo
                while GPIO.input(pin) == GPIO.LOW and time.time() < timeout:
                    time.sleep(0.01)
                
                return name
    
    return None

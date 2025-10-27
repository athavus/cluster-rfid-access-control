import RPi.GPIO as GPIO
import time

BUTTON_GPIO = {'left': 17, 'right': 27, 'ok': 22}

GPIO.setmode(GPIO.BCM)
for pin in BUTTON_GPIO.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def read_button():
    """
    ----------------------------------------------------------------------
    @brief Lê o estado dos botões físicos conectados aos pinos GPIO.

    Verifica sequencialmente o estado dos pinos configurados para cada botão
    (esquerda, direita e ok/confirmar), realizando debounce simples para evitar
    múltiplas leituras por clique. Retorna o identificador do botão pressionado.

    Os pinos devem estar previamente configurados no modo BCM e com pull-down.

    @return
        - 'left'   : Se o botão da esquerda foi pressionado.
        - 'right'  : Se o botão da direita foi pressionado.
        - 'ok'     : Se o botão de confirmação foi pressionado.
        - None     : Se nenhum botão está pressionado.
    ----------------------------------------------------------------------
    """
    for name, pin in BUTTON_GPIO.items():
        if GPIO.input(pin) == GPIO.HIGH:
            time.sleep(0.18)  # debounce simples
            while GPIO.input(pin) == GPIO.HIGH:
                pass  # aguarda soltar botão
            return name
    return None


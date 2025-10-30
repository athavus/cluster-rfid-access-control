"""
Manipulador de GPIO para Raspberry Pi 5
"""

try:
    # Para Raspberry Pi 5, usar rpi-lgpio
    import RPi.GPIO as GPIO

    # Configuração dos pinos (referências BCM e BOARD)
    LED_EXTERNAL_PIN_BCM = 17  # GPIO17 (pino 11 físico)
    LED_INTERNAL_PIN_BCM = 18  # GPIO18 (pino 12 físico) - LED interno da placa
    LED_EXTERNAL_PIN_BOARD = 11  # Pino físico 11 (equivale ao BCM17)
    LED_INTERNAL_PIN_BOARD = 12  # Pino físico 12 (equivale ao BCM18)

    # Pinos efetivos ativos serão definidos na inicialização
    _ACTIVE_LED_EXTERNAL_PIN = None
    _ACTIVE_LED_INTERNAL_PIN = None
    _INITIALIZED = False

    def _initialize_gpio_if_needed():
        """Inicializa GPIO uma única vez, respeitando o modo já definido (BOARD/BCM)."""
        global _INITIALIZED, _ACTIVE_LED_EXTERNAL_PIN, _ACTIVE_LED_INTERNAL_PIN
        if _INITIALIZED:
            return
        current_mode = GPIO.getmode()
        # Não force um modo se já houver um definido para evitar
        # "A different mode has already been set!"
        if current_mode is None:
            # Escolha padrão: BCM quando não houver modo definido
            GPIO.setmode(GPIO.BCM)
            current_mode = GPIO.BCM

        GPIO.setwarnings(False)

        if current_mode == GPIO.BOARD:
            _ACTIVE_LED_EXTERNAL_PIN = LED_EXTERNAL_PIN_BOARD
            _ACTIVE_LED_INTERNAL_PIN = LED_INTERNAL_PIN_BOARD
        else:
            # Trata BCM e quaisquer outros casos como BCM
            _ACTIVE_LED_EXTERNAL_PIN = LED_EXTERNAL_PIN_BCM
            _ACTIVE_LED_INTERNAL_PIN = LED_INTERNAL_PIN_BCM

        # Configurar pinos como saída
        GPIO.setup(_ACTIVE_LED_EXTERNAL_PIN, GPIO.OUT)
        GPIO.setup(_ACTIVE_LED_INTERNAL_PIN, GPIO.OUT)

        # Iniciar com LEDs desligados
        GPIO.output(_ACTIVE_LED_EXTERNAL_PIN, GPIO.LOW)
        GPIO.output(_ACTIVE_LED_INTERNAL_PIN, GPIO.LOW)

        _INITIALIZED = True
        print("GPIO inicializado com sucesso")

    GPIO_AVAILABLE = True

except (ImportError, RuntimeError) as e:
    print(f"GPIO não disponível: {e}")
    print("Rodando em modo de simulação")
    GPIO_AVAILABLE = False
    # Fallback para simulação
    LED_EXTERNAL_PIN_BCM = 17
    LED_INTERNAL_PIN_BCM = 18
    LED_EXTERNAL_PIN_BOARD = 11
    LED_INTERNAL_PIN_BOARD = 12
    _ACTIVE_LED_EXTERNAL_PIN = LED_EXTERNAL_PIN_BCM
    _ACTIVE_LED_INTERNAL_PIN = LED_INTERNAL_PIN_BCM
    _INITIALIZED = True
    def _initialize_gpio_if_needed():
        return

class GPIOController:
    """Controlador de GPIO com fallback para simulação"""
    
    @staticmethod
    def set_led(pin: int, state: bool) -> bool:
        """
        Liga ou desliga um LED
        
        Args:
            pin: Número do pino GPIO
            state: True para ligar, False para desligar
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            if GPIO_AVAILABLE:
                _initialize_gpio_if_needed()
                if state:
                    GPIO.output(pin, GPIO.HIGH)
                else:
                    GPIO.output(pin, GPIO.LOW)
                return True
            else:
                # Modo simulação
                if state:
                    print(f"[SIMULAÇÃO] LED no pino {pin}: ON")
                else:
                    print(f"[SIMULAÇÃO] LED no pino {pin}: OFF")
                return True
        except Exception as e:
            print(f"Erro ao controlar GPIO: {e}")
            return False
    
    @staticmethod
    def get_pin(led_type: str) -> int:
        """Retorna o pino GPIO baseado no tipo de LED"""
        # Garante inicialização para termos os pinos ativos corretos
        if GPIO_AVAILABLE:
            _initialize_gpio_if_needed()
        if led_type == "internal":
            return _ACTIVE_LED_INTERNAL_PIN
        else:
            return _ACTIVE_LED_EXTERNAL_PIN
    
    @staticmethod
    def cleanup():
        """Limpa as configurações de GPIO"""
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                print("GPIO cleanup realizado")
            except:
                pass



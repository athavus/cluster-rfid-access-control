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
    # Mapeamento básico BCM -> BOARD para header de 40 pinos
    _BCM_TO_BOARD = {
        2: 3, 3: 5, 4: 7, 17: 11, 27: 13, 22: 15,
        10: 19, 9: 21, 11: 23, 0: 27, 1: 28, 5: 29,
        6: 31, 13: 33, 19: 35, 26: 37, 14: 8, 15: 10,
        18: 12, 23: 16, 24: 18, 25: 22, 8: 24, 7: 26,
        12: 32, 16: 36, 20: 38, 21: 40
    }
    
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
        if GPIO_AVAILABLE:
            try:
                _initialize_gpio_if_needed()
                current_mode = GPIO.getmode()
                
                if current_mode is None:
                    # Se não há modo definido, define como BCM
                    GPIO.setmode(GPIO.BCM)
                    current_mode = GPIO.BCM
                
                effective_pin = pin
                if current_mode == GPIO.BOARD:
                    # Converte do BCM informado pelo cliente para BOARD
                    if pin not in GPIOController._BCM_TO_BOARD:
                        raise ValueError(f"BCM {pin} não mapeado para BOARD")
                    effective_pin = GPIOController._BCM_TO_BOARD[pin]
                
                # Verifica se o pino não está em uso pelo servo (pino 12)
                if effective_pin == 12:
                    raise RuntimeError(f"Pino {pin} (BCM 12) está reservado para o servo motor. Use outro pino para o LED.")
                
                # Garante que o pino informado esteja configurado como saída
                # Tenta configurar o pino, ignorando erros se já estiver configurado
                try:
                    GPIO.setup(effective_pin, GPIO.OUT, initial=GPIO.LOW)
                except RuntimeError as e:
                    error_msg = str(e).lower()
                    # Se o erro for sobre pino já configurado ou modo, tenta continuar
                    if "already" in error_msg or "mode" in error_msg:
                        # Pino já configurado, pode tentar usar mesmo assim
                        pass
                    elif "not allocated" in error_msg:
                        # Erro específico do lgpio - pode ser conflito com servo
                        raise RuntimeError(f"Pino {pin} (BCM) não está disponível. Pode estar em uso pelo servo motor (pino 12) ou outro processo.")
                    else:
                        raise
                except Exception as e:
                    error_msg = str(e).lower()
                    if "not allocated" in error_msg:
                        raise RuntimeError(f"Pino {pin} (BCM) não está disponível. Pode estar em uso por outro processo.")
                    elif "already" in error_msg or "mode" in error_msg:
                        # Pino já configurado, pode continuar
                        pass
                    else:
                        raise
                
                # Tenta controlar o LED
                try:
                    if state:
                        GPIO.output(effective_pin, GPIO.HIGH)
                    else:
                        GPIO.output(effective_pin, GPIO.LOW)
                except RuntimeError as e:
                    # Se falhar ao controlar, pode ser que o pino esteja em uso
                    error_msg = str(e).lower()
                    if "not allocated" in error_msg:
                        raise RuntimeError(f"Pino {pin} (BCM) não está disponível. Pode estar em uso por outro processo (ex: servo no pino 12).")
                    raise
                
                return True
            except Exception as e:
                error_msg = str(e)
                print(f"[GPIO] Erro ao controlar LED no pino {pin}: {error_msg}")
                raise RuntimeError(f"Falha no GPIO: {error_msg}")
        else:
            # Modo simulação
            if state:
                print(f"[SIMULAÇÃO] LED no pino {pin}: ON")
            else:
                print(f"[SIMULAÇÃO] LED no pino {pin}: OFF")
            return True
    
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




"""
Manipulador de GPIO para Raspberry Pi 5
Usa rpi-lgpio em vez de RPi.GPIO
"""

try:
    # Para Raspberry Pi 5, usar rpi-lgpio
    import RPi.GPIO as GPIO
    
    # Configuração dos pinos
    LED_EXTERNAL_PIN = 17  # GPIO17 (pino 11 físico)
    LED_INTERNAL_PIN = 18  # GPIO18 (pino 12 físico) - LED interno da placa
    
    # Inicializar GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Configurar pinos como saída
    GPIO.setup(LED_EXTERNAL_PIN, GPIO.OUT)
    GPIO.setup(LED_INTERNAL_PIN, GPIO.OUT)
    
    # Iniciar com LEDs desligados
    GPIO.output(LED_EXTERNAL_PIN, GPIO.LOW)
    GPIO.output(LED_INTERNAL_PIN, GPIO.LOW)
    
    GPIO_AVAILABLE = True
    print("GPIO inicializado com sucesso")
    
except (ImportError, RuntimeError) as e:
    print(f"GPIO não disponível: {e}")
    print("Rodando em modo de simulação")
    GPIO_AVAILABLE = False
    LED_EXTERNAL_PIN = 17
    LED_INTERNAL_PIN = 18

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
        if led_type == "internal":
            return LED_INTERNAL_PIN
        else:
            return LED_EXTERNAL_PIN
    
    @staticmethod
    def cleanup():
        """Limpa as configurações de GPIO"""
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                print("GPIO cleanup realizado")
            except:
                pass


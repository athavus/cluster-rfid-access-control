"""
Biblioteca SIMPLIFICADA para controle de servo motor SG90 usando RPi.GPIO
SEM gpio_manager - configuração direta
"""

import RPi.GPIO as GPIO
import time

class ServoSG90:
    """
    Classe para controlar servo motor SG90
    
    O servo SG90 opera com:
    - Frequência: 50Hz (período de 20ms)
    - Pulso para 0°: ~1ms (5% duty cycle)
    - Pulso para 90°: ~1.5ms (7.5% duty cycle)
    - Pulso para 180°: ~2ms (10% duty cycle)
    """
    
    def __init__(self, gpio_pin, initial_angle=90):
        """
        Inicializa o servo motor
        
        Args:
            gpio_pin (int): Número do pino GPIO (numeração BCM)
            initial_angle (int): Ângulo inicial (0-180)
        """
        self.gpio_pin = gpio_pin
        self.frequency = 50  # 50Hz para servos
        
        # Configurar modo GPIO se ainda não foi configurado
        try:
            current_mode = GPIO.getmode()
            if current_mode is None:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                print(f"[Servo] Modo GPIO BCM configurado")
            elif current_mode != GPIO.BCM:
                print(f"[Servo] Modo GPIO já configurado: {current_mode}")
            
            # Configurar pino
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            print(f"[Servo] Pino {gpio_pin} configurado como OUTPUT")
            
            # Inicializar PWM
            self.pwm = GPIO.PWM(self.gpio_pin, self.frequency)
            
            # Mover para posição inicial
            self.current_angle = initial_angle
            self._set_angle(initial_angle)
            time.sleep(0.3)  # Aguardar servo estabilizar
            
            print(f"[Servo] Inicializado no pino {gpio_pin} em {initial_angle}°")
            
        except Exception as e:
            print(f"[Servo] ERRO ao inicializar: {e}")
            raise
    
    def _angle_to_duty_cycle(self, angle):
        """
        Converte ângulo (0-180) para duty cycle (2-12%)
        
        Args:
            angle (int): Ângulo desejado (0-180)
        
        Returns:
            float: Duty cycle em porcentagem
        """
        # Limitar ângulo entre 0 e 180
        angle = max(0, min(180, angle))
        
        # Mapear ângulo para duty cycle
        # 0° = 2% (1ms), 90° = 7% (1.5ms), 180° = 12% (2ms)
        duty_cycle = 2 + (angle / 180.0) * 10
        return duty_cycle
    
    def _set_angle(self, angle):
        """
        Move o servo para o ângulo especificado de forma rápida
        
        Args:
            angle (int): Ângulo desejado (0-180)
        """
        duty_cycle = self._angle_to_duty_cycle(angle)
        
        # Iniciar PWM e enviar pulsos
        self.pwm.start(duty_cycle)
        time.sleep(0.4)  # Tempo para movimento
        self.pwm.ChangeDutyCycle(0)  # Parar sinais para evitar tremor
    
    def move_to_angle_and_return(self, angle, hold_time=5):
        """
        Move o servo para o ângulo especificado, mantém por um tempo
        e retorna à posição original
        
        Args:
            angle (int): Ângulo de destino (0-180)
            hold_time (float): Tempo para manter o ângulo em segundos (padrão: 5)
        """
        original_angle = self.current_angle
        
        print(f"[Servo] Movendo de {original_angle}° para {angle}°...")
        self._set_angle(angle)
        self.current_angle = angle
        
        print(f"[Servo] Mantendo posição em {angle}° por {hold_time} segundos...")
        time.sleep(hold_time)
        
        print(f"[Servo] Retornando para {original_angle}°...")
        self._set_angle(original_angle)
        self.current_angle = original_angle
        
        print("[Servo] Movimento concluído!")
    
    def cleanup(self):
        """Libera os recursos do servo"""
        try:
            self.pwm.stop()
            GPIO.cleanup(self.gpio_pin)
            print(f"[Servo] Pino {self.gpio_pin} liberado")
        except Exception as e:
            print(f"[Servo] Erro ao liberar recursos: {e}")


def rotate_servo(gpio_pin, angle, hold_time=5, return_to=90):
    """
    Função de conveniência para rotacionar servo rapidamente
    
    Args:
        gpio_pin (int): Pino GPIO (BCM)
        angle (int): Ângulo de destino (0-180)
        hold_time (float): Tempo em segundos para manter o ângulo
        return_to (int): Ângulo para retornar (padrão: 90)
    """
    servo = ServoSG90(gpio_pin, initial_angle=return_to)
    try:
        servo.move_to_angle_and_return(angle, hold_time)
    finally:
        servo.cleanup()

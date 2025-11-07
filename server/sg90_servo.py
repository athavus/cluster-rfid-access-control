"""
Biblioteca para controle de servo motor SG90 usando lgpio
Compatível com Raspberry Pi
"""

import lgpio
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
        self.chip = lgpio.gpiochip_open(0)
        
        # Configurar o pino como saída
        lgpio.gpio_claim_output(self.chip, self.gpio_pin)
        
        # Mover para posição inicial
        self.current_angle = initial_angle
        self._set_angle(initial_angle)
        time.sleep(0.3)  # Aguardar servo estabilizar
    
    def _angle_to_pulse_width(self, angle):
        """
        Converte ângulo (0-180) para largura de pulso em microssegundos
        
        Args:
            angle (int): Ângulo desejado (0-180)
            
        Returns:
            int: Largura do pulso em microssegundos
        """
        # Limitar ângulo entre 0 e 180
        angle = max(0, min(180, angle))
        
        # Mapear ângulo para largura de pulso
        # 0° = 1000µs (1ms), 180° = 2000µs (2ms)
        pulse_width = int(1000 + (angle / 180.0) * 1000)
        
        return pulse_width
    
    def _set_angle(self, angle):
        """
        Move o servo para o ângulo especificado de forma rápida
        
        Args:
            angle (int): Ângulo desejado (0-180)
        """
        pulse_width = self._angle_to_pulse_width(angle)
        
        # Enviar apenas pulsos suficientes para movimento rápido
        # Reduzido para evitar tremor
        for _ in range(20):  # ~20 pulsos (0.4 segundos)
            lgpio.tx_pulse(self.chip, self.gpio_pin, pulse_width, 20000 - pulse_width)
            time.sleep(0.02)  # 20ms = 50Hz
    
    def move_continuous(self, angle1, angle2, wait_time=1, cycles=None):
        """
        Move o servo continuamente entre dois ângulos
        
        Args:
            angle1 (int): Primeiro ângulo (normalmente posição inicial)
            angle2 (int): Segundo ângulo (ângulo de destino)
            wait_time (float): Tempo de espera em cada posição em segundos (padrão: 1)
            cycles (int): Número de ciclos (None = infinito)
        """
        cycle_count = 0
        try:
            while True:
                # Ir para angle2 (ex: 180°)
                print(f"Movendo para {angle2}°...")
                self._set_angle(angle2)
                self.current_angle = angle2
                time.sleep(wait_time)
                
                # Voltar para angle1 (ex: 0° ou 90°)
                print(f"Voltando para {angle1}°...")
                self._set_angle(angle1)
                self.current_angle = angle1
                time.sleep(wait_time)
                
                cycle_count += 1
                if cycles is not None and cycle_count >= cycles:
                    break
                    
        except KeyboardInterrupt:
            print("\nMovimento interrompido pelo usuário")
            # Retornar para posição inicial
            self._set_angle(angle1)
    
    def move_to_angle_and_return(self, angle, hold_time=5):
        """
        Move o servo para o ângulo especificado, mantém por um tempo
        e retorna à posição original (versão rápida)
        
        Args:
            angle (int): Ângulo de destino (0-180)
            hold_time (float): Tempo para manter o ângulo em segundos (padrão: 5)
        """
        original_angle = self.current_angle
        
        print(f"Movendo de {original_angle}° para {angle}°...")
        self._set_angle(angle)
        self.current_angle = angle
        
        print(f"Mantendo posição em {angle}° por {hold_time} segundos...")
        time.sleep(hold_time)
        
        print(f"Retornando para {original_angle}°...")
        self._set_angle(original_angle)
        self.current_angle = original_angle
        
        print("Movimento concluído!")
    
    def cleanup(self):
        """
        Libera os recursos do GPIO
        """
        lgpio.gpiochip_close(self.chip)
        print("GPIO liberado")


# Função auxiliar para uso rápido - movimento contínuo
def rotate_servo_continuous(gpio_pin, angle_from=90, angle_to=180, wait_time=1, cycles=None):
    """
    Função para rotacionar servo continuamente entre duas posições
    
    Args:
        gpio_pin (int): Pino GPIO (BCM)
        angle_from (int): Ângulo inicial (padrão: 90)
        angle_to (int): Ângulo de destino (padrão: 180)
        wait_time (float): Tempo em cada posição em segundos (padrão: 1)
        cycles (int): Número de ciclos (None = infinito)
    """
    servo = ServoSG90(gpio_pin, initial_angle=angle_from)
    try:
        servo.move_continuous(angle_from, angle_to, wait_time, cycles)
    finally:
        servo.cleanup()


# Função auxiliar original
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


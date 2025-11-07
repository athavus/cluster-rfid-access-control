
"""
Handler para controle do servo motor SG90 (fechadura)
Controla o servo no pino 12 para simular abertura de porta
"""

import threading
from typing import Optional
from datetime import datetime
from database import SessionLocal

# Tentar importar biblioteca do servo
try:
    from sg90_servo import ServoSG90
    SERVO_AVAILABLE = True
    print("[Servo] Biblioteca sg90_servo importada com sucesso")
except ImportError as e:
    SERVO_AVAILABLE = False
    print(f"[Servo] sg90_servo não disponível - rodando em modo simulação: {e}")


class ServoHandler:
    """Handler para gerenciar servo motor (fechadura)"""
    
    def __init__(self, gpio_pin: int = 12):
        """
        Inicializa o handler do servo
        
        Args:
            gpio_pin: Pino GPIO onde o servo está conectado (padrão: 12)
        """
        self.gpio_pin = gpio_pin
        self.servo: Optional[ServoSG90] = None
        self.is_open = False
        self.is_moving = False
        self.last_open_time: Optional[datetime] = None
        
        if SERVO_AVAILABLE:
            try:
                print(f"[Servo] Tentando inicializar servo no pino GPIO {gpio_pin}...")
                # Inicializa o servo na posição fechada (90 graus)
                self.servo = ServoSG90(gpio_pin, initial_angle=90)
                print(f"[Servo] ✓ Servo inicializado com sucesso no pino {gpio_pin}")
            except PermissionError as e:
                print(f"[Servo] ✗ ERRO DE PERMISSÃO: {e}")
                print("[Servo] Execute com: sudo uvicorn main:app --host 0.0.0.0 --port 8000")
                self.servo = None
            except Exception as e:
                print(f"[Servo] ✗ Erro ao inicializar servo: {e}")
                print(f"[Servo] Tipo do erro: {type(e).__name__}")
                self.servo = None
        else:
            print("[Servo] Servo não disponível (biblioteca não encontrada)")
    
    def open_door(self, hold_time: float = 10.0) -> bool:
        """
        Abre a fechadura (gira o servo para 180°) e mantém por hold_time segundos
        
        Args:
            hold_time: Tempo em segundos para manter a porta aberta (padrão: 5)
        
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if self.is_moving:
            print("[Servo] Servo já está em movimento, ignorando comando")
            return False
        
        if not self.servo:
            print("[Servo] ⚠️ Modo simulação - abrindo porta (virtual)")
            self.is_open = True
            self.last_open_time = datetime.utcnow()
            # Simular tempo de abertura
            import time
            time.sleep(hold_time)
            self.is_open = False
            return True
        
        self.is_moving = True
        
        def open_thread():
            try:
                print(f"[Servo] → Abrindo porta (movendo para 180°)...")
                self.is_open = True
                self.last_open_time = datetime.utcnow()
                
                # Usar método move_to_angle_and_return do servo
                self.servo.move_to_angle_and_return(180, hold_time=hold_time)
                
                self.is_open = False
                print(f"[Servo] ← Porta fechada novamente (retornou para 90°)")
            except Exception as e:
                print(f"[Servo] ✗ Erro ao abrir porta: {e}")
                self.is_open = False
            finally:
                self.is_moving = False
        
        # Executa em thread separada para não bloquear
        thread = threading.Thread(target=open_thread, daemon=True)
        thread.start()
        
        return True
    
    def get_status(self) -> dict:
        """
        Retorna o status atual do servo
        
        Returns:
            dict: Status do servo (is_open, is_moving, last_open_time)
        """
        return {
            "is_open": self.is_open,
            "is_moving": self.is_moving,
            "last_open_time": self.last_open_time.isoformat() if self.last_open_time else None,
            "gpio_pin": self.gpio_pin,
            "available": SERVO_AVAILABLE and self.servo is not None
        }
    
    def cleanup(self):
        """Libera recursos do servo"""
        if self.servo:
            try:
                self.servo.cleanup()
                print("[Servo] Recursos liberados")
            except Exception as e:
                print(f"[Servo] Erro ao limpar recursos: {e}")


# Instância global
_servo_handler: Optional[ServoHandler] = None

def init_servo_handler(gpio_pin: int = 12) -> ServoHandler:
    """Inicializa o handler global do servo"""
    global _servo_handler
    print(f"[Servo Handler] Inicializando no pino GPIO {gpio_pin}...")
    _servo_handler = ServoHandler(gpio_pin)
    return _servo_handler

def get_servo_handler() -> Optional[ServoHandler]:
    """Retorna a instância global do handler do servo"""
    return _servo_handler

def cleanup_servo():
    """Limpa recursos do servo"""
    global _servo_handler
    if _servo_handler:
        _servo_handler.cleanup()
        _servo_handler = None

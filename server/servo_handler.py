"""
Handler para controle do servo motor SG90 (fechadura)

Controla o servo no pino 12 para simular abertura de porta

VERSÃO 2: Executa script diagnostico_servo.py via subprocess
"""

import threading
import subprocess
import os
from typing import Optional
from datetime import datetime
from database import SessionLocal

class ServoHandler:
    """Handler para gerenciar servo motor (fechadura) via script externo"""

    def __init__(self, gpio_pin: int = 12, script_path: str = None):
        """
        Inicializa o handler do servo

        Args:
            gpio_pin: Pino GPIO onde o servo está conectado (padrão: 12)
            script_path: Caminho para o script de controle do servo
        """
        self.gpio_pin = gpio_pin
        self.is_open = False
        self.is_moving = False
        self.last_open_time: Optional[datetime] = None
        
        # Determinar caminho do script
        if script_path is None:
            # Assumir que está no mesmo diretório
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.script_path = os.path.join(current_dir, "diagnostico_servo.py")
        else:
            self.script_path = script_path
        
        # Verificar se script existe
        if os.path.exists(self.script_path):
            print(f"[Servo Handler] Script encontrado: {self.script_path}")
        else:
            print(f"[Servo Handler] ⚠️  Script não encontrado: {self.script_path}")
        
        print(f"[Servo Handler] Inicializado no pino GPIO {gpio_pin}")

    def open_door(self, hold_time: float = 5.0) -> bool:
        """
        Abre a fechadura (gira o servo para 180°) e mantém por hold_time segundos
        
        Executa o script diagnostico_servo.py via subprocess

        Args:
            hold_time: Tempo em segundos para manter a porta aberta (padrão: 5)

        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if self.is_moving:
            print("[Servo] Servo já está em movimento, ignorando comando")
            return False

        if not os.path.exists(self.script_path):
            print(f"[Servo] ⚠️  Script não encontrado: {self.script_path}")
            return False

        self.is_moving = True

        def open_thread():
            try:
                print(f"[Servo] → Executando script: {self.script_path}")
                self.is_open = True
                self.last_open_time = datetime.utcnow()

                # Executar script com sudo
                result = subprocess.run(
                    ["sudo", "python3", self.script_path],
                    capture_output=True,
                    text=True,
                    timeout=30  # Timeout de 30 segundos
                )

                # Exibir saída do script
                if result.stdout:
                    print("[Servo] Saída do script:")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            print(f"  {line}")

                if result.returncode == 0:
                    print("[Servo] ✓ Script executado com sucesso")
                else:
                    print(f"[Servo] ✗ Script falhou com código {result.returncode}")
                    if result.stderr:
                        print(f"[Servo] Erro: {result.stderr}")

                self.is_open = False
                print(f"[Servo] ← Porta fechada novamente")

            except subprocess.TimeoutExpired:
                print(f"[Servo] ✗ Timeout ao executar script (>30s)")
                self.is_open = False
            except Exception as e:
                print(f"[Servo] ✗ Erro ao executar script: {e}")
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
            "available": os.path.exists(self.script_path),
            "script_path": self.script_path
        }

    def cleanup(self):
        """Libera recursos do servo (nenhum recurso persistente nesta versão)"""
        print("[Servo] Handler limpo")


# Instância global
_servo_handler: Optional[ServoHandler] = None


def init_servo_handler(gpio_pin: int = 12, script_path: str = None) -> ServoHandler:
    """Inicializa o handler global do servo"""
    global _servo_handler
    print(f"[Servo Handler] Inicializando no pino GPIO {gpio_pin}...")
    _servo_handler = ServoHandler(gpio_pin, script_path)
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

# gpio_manager.py
"""
Gerenciador centralizado de GPIO para evitar conflitos entre módulos
Este módulo DEVE ser importado PRIMEIRO por todos os outros que usam GPIO
VERSÃO CORRIGIDA - verifica modo antes de cada operação
"""

import RPi.GPIO as GPIO
from typing import Optional

class GPIOManager:
    """Singleton para gerenciar GPIO de forma centralizada"""
    _instance: Optional['GPIOManager'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not GPIOManager._initialized:
            self._setup_gpio()
            GPIOManager._initialized = True
    
    def _setup_gpio(self):
        """Configura GPIO uma única vez"""
        self._ensure_mode_set()
        print("[GPIO Manager] GPIO Manager inicializado com sucesso")
    
    def _ensure_mode_set(self):
        """Garante que o modo GPIO está configurado"""
        try:
            current_mode = GPIO.getmode()
            if current_mode is None:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                print("[GPIO Manager] GPIO configurado em modo BCM")
            elif current_mode == GPIO.BCM:
                GPIO.setwarnings(False)
                # Modo já está correto
                pass
            elif current_mode == GPIO.BOARD:
                print(f"[GPIO Manager] Aviso: GPIO já estava em modo BOARD, mantendo")
                GPIO.setwarnings(False)
        except Exception as e:
            print(f"[GPIO Manager] Erro ao configurar GPIO: {e}")
            raise
    
    def setup_pin(self, pin: int, mode: int, initial: int = GPIO.LOW):
        """
        Configura um pino de forma segura
        
        Args:
            pin: Número do pino (BCM)
            mode: GPIO.OUT ou GPIO.IN
            initial: Estado inicial (para pinos de saída)
        """
        try:
            # Garantir que modo está configurado ANTES de setup
            self._ensure_mode_set()
            
            GPIO.setup(pin, mode, initial=initial)
            print(f"[GPIO Manager] Pino {pin} configurado como {'OUTPUT' if mode == GPIO.OUT else 'INPUT'}")
        except Exception as e:
            print(f"[GPIO Manager] Erro ao configurar pino {pin}: {e}")
            raise
    
    def cleanup_pin(self, pin: int):
        """Limpa um pino específico"""
        try:
            GPIO.cleanup(pin)
            print(f"[GPIO Manager] Pino {pin} limpo")
        except Exception as e:
            print(f"[GPIO Manager] Erro ao limpar pino {pin}: {e}")
    
    def cleanup_all(self):
        """Limpa TODOS os pinos GPIO"""
        try:
            GPIO.cleanup()
            print("[GPIO Manager] Todos os pinos GPIO foram limpos")
            GPIOManager._initialized = False
        except Exception as e:
            print(f"[GPIO Manager] Erro ao limpar GPIO: {e}")
    
    @staticmethod
    def get_instance() -> 'GPIOManager':
        """Retorna a instância singleton"""
        if GPIOManager._instance is None:
            GPIOManager._instance = GPIOManager()
        return GPIOManager._instance

# Instância global para facilitar o uso
gpio_manager = GPIOManager()

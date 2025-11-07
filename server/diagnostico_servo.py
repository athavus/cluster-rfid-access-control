#!/usr/bin/env python3
"""
Script de diagnóstico CORRIGIDO para verificar GPIO e Servo
Execute com: sudo python3 diagnostico_servo.py
"""

import sys
import os

print("=" * 60)
print("DIAGNÓSTICO DO SERVO - Raspberry Pi")
print("=" * 60)

# 1. Verificar permissões
print("\n[1] Verificando permissões...")
if os.geteuid() != 0:
    print("    ✗ Não está rodando como root (sudo)")
    print("    → Execute: sudo python3 diagnostico_servo.py")
else:
    print("    ✓ Rodando como root")

# 2. Verificar Python version
print("\n[2] Versão do Python:")
print(f"    {sys.version}")

# 3. Tentar importar RPi.GPIO
print("\n[3] Testando importação de RPi.GPIO...")
try:
    import RPi.GPIO as GPIO
    print("    ✓ RPi.GPIO disponível")
    print(f"    Versão: {GPIO.VERSION}")
except ImportError as e:
    print(f"    ✗ RPi.GPIO não disponível: {e}")
    print("    → Instalar com: sudo pip3 install RPi.GPIO")
    sys.exit(1)

# 4. Verificar modo GPIO
print("\n[4] Verificando modo GPIO atual...")
try:
    current_mode = GPIO.getmode()
    if current_mode is None:
        print("    ℹ GPIO não configurado ainda")
    elif current_mode == GPIO.BCM:
        print("    ✓ Modo BCM já configurado")
    elif current_mode == GPIO.BOARD:
        print("    ⚠️ Modo BOARD configurado (esperado BCM)")
    
    # Configurar modo BCM se necessário
    if current_mode is None:
        GPIO.setmode(GPIO.BCM)
        print("    ✓ Modo BCM configurado")
    
    GPIO.setwarnings(False)
except Exception as e:
    print(f"    ✗ Erro ao verificar GPIO: {e}")
    sys.exit(1)

# 5. Testar configuração do pino 12
print("\n[5] Testando configuração do pino GPIO 12...")
try:
    GPIO.setup(12, GPIO.OUT)
    print("    ✓ Pino 12 configurado como OUTPUT")
except Exception as e:
    print(f"    ✗ Erro ao configurar pino 12: {e}")
    GPIO.cleanup()
    sys.exit(1)

# 6. Testar PWM no pino 12
print("\n[6] Testando PWM no pino 12...")
pwm_test = None
try:
    pwm_test = GPIO.PWM(12, 50)  # 50Hz para servo
    print("    ✓ PWM criado com sucesso (50Hz)")
    
    # Testar início do PWM
    pwm_test.start(7.5)  # 7.5% duty cycle = 90 graus
    print("    ✓ PWM iniciado (posição 90°)")
    
    import time
    time.sleep(0.5)
    
    pwm_test.stop()
    print("    ✓ PWM parado")
    
    # IMPORTANTE: Limpar TUDO antes de criar o servo
    print("    ℹ Limpando PWM e GPIO para próximo teste...")
    del pwm_test  # Deletar objeto PWM
    GPIO.cleanup()
    print("    ✓ GPIO limpo")
    
except Exception as e:
    print(f"    ✗ Erro ao testar PWM: {e}")
    if pwm_test:
        pwm_test.stop()
    GPIO.cleanup()
    sys.exit(1)

# 7. Tentar importar sg90_servo
print("\n[7] Testando importação de sg90_servo.py...")
try:
    # Adicionar diretório atual ao path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from sg90_servo import ServoSG90
    print("    ✓ sg90_servo.py importado com sucesso")
    
    # Verificar se a classe existe
    print(f"    ✓ Classe ServoSG90 encontrada: {ServoSG90}")
    
except ImportError as e:
    print(f"    ✗ Erro ao importar sg90_servo: {e}")
    print("    → Verifique se sg90_servo.py existe no diretório")
    sys.exit(1)
except Exception as e:
    print(f"    ✗ Erro inesperado: {e}")
    sys.exit(1)

# 8. Testar criação do servo
print("\n[8] Testando criação de objeto ServoSG90...")
try:
    servo = ServoSG90(12, initial_angle=90)
    print("    ✓ ServoSG90 criado com sucesso")
    print(f"    Pino: {servo.gpio_pin}")
    print(f"    Ângulo atual: {servo.current_angle}°")
    
    # Testar movimento
    print("\n[9] Testando movimento do servo...")
    print("    → Movendo para 45°...")
    servo._set_angle(45)
    
    import time
    time.sleep(4)
    
    print("    → Movendo para 90°...")
    servo._set_angle(90)
    
    time.sleep(1) 
    
    print("    ✓ Movimentos executados com sucesso!")
    
    # Limpar
    servo.cleanup()
    
except PermissionError as e:
    print(f"    ✗ ERRO DE PERMISSÃO: {e}")
    print("    → Execute com sudo: sudo python3 diagnostico_servo.py")
    GPIO.cleanup()
    sys.exit(1)
except Exception as e:
    print(f"    ✗ Erro ao criar/testar servo: {e}")
    print(f"    Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    GPIO.cleanup()
    sys.exit(1)

# Sucesso!
print("\n" + "=" * 60)
print("✓ DIAGNÓSTICO COMPLETO - TUDO FUNCIONANDO!")
print("=" * 60)
print("\nSeu servo está configurado corretamente.")
print("\nPara rodar seu servidor:")
print("\n  1. Com venv ativado:")
print("     sudo $(which python3) -m uvicorn main:app --host 0.0.0.0 --port 8000")
print("\n  2. Sem venv:")
print("     sudo uvicorn main:app --host 0.0.0.0 --port 8000")
print("=" * 60)

GPIO.cleanup()

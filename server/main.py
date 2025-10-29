from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from consumer import start_consumer_thread
from shared import received_messages
from database import get_db, init_db, LEDHistory, DeviceStatus
from schemas import (
    LEDCommand, LEDHistoryResponse, DeviceStatusResponse
)
from gpio_handler import GPIOController, GPIO_AVAILABLE

# Inicializar banco de dados
init_db()

# Iniciar consumer do RabbitMQ em thread separada
start_consumer_thread()

# Criar aplicação FastAPI
app = FastAPI(
    title="Raspberry Pi 5 IoT API",
    description="API para gerenciamento de cluster Raspberry Pi com controle de LEDs e health check",
    version="2.0.0"
)

# Configurar CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============= ENDPOINTS DE CONTROLE DE LED =============

@app.post("/api/led/control", tags=["LED Control"])
def control_led(command: LEDCommand, db: Session = Depends(get_db)):
    """
    Controla um LED (interno ou externo) da Raspberry Pi 5
    
    - **status**: "ON" ou "OFF"
    - **raspberry_id**: ID da Raspberry (padrão: 1)
    - **led_type**: "internal" ou "external" (padrão: "external")
    """
    raspberry_id = command.raspberry_id
    led_type = command.led_type.lower()
    
    if led_type not in ["internal", "external"]:
        raise HTTPException(
            status_code=400, 
            detail="led_type deve ser 'internal' ou 'external'"
        )
    
    if command.status.upper() not in ["ON", "OFF"]:
        raise HTTPException(
            status_code=400, 
            detail="status deve ser 'ON' ou 'OFF'"
        )
    
    # Obter o pino correto
    pin = GPIOController.get_pin(led_type)
    
    # Controlar o LED
    led_state = command.status.upper() == "ON"
    success = GPIOController.set_led(pin, led_state)
    
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Erro ao controlar LED"
        )
    
    # Atualizar status no banco
    device = db.query(DeviceStatus).filter(
        DeviceStatus.raspberry_id == raspberry_id
    ).first()
    
    if device:
        if led_type == "internal":
            device.led_internal_status = led_state
        else:
            device.led_external_status = led_state
        device.last_update = datetime.utcnow()
    else:
        device = DeviceStatus(
            raspberry_id=raspberry_id,
            led_internal_status=led_state if led_type == "internal" else False,
            led_external_status=led_state if led_type == "external" else False
        )
        db.add(device)
    
    # Registrar no histórico
    history = LEDHistory(
        raspberry_id=raspberry_id,
        led_type=led_type,
        pin=pin,
        action=command.status.upper()
    )
    db.add(history)
    db.commit()
    
    return {
        "message": f"LED {led_type} {'ligado' if led_state else 'desligado'}",
        "raspberry_id": raspberry_id,
        "led_type": led_type,
        "pin": pin,
        "status": command.status.upper(),
        "gpio_available": GPIO_AVAILABLE,
        "timestamp": datetime.utcnow()
    }

@app.post("/api/led/{led_type}/on", tags=["LED Control"])
def led_on(
    led_type: str,
    raspberry_id: int = Query(1, description="ID da Raspberry Pi"),
    db: Session = Depends(get_db)
):
    """Atalho para ligar LED (interno ou externo)"""
    return control_led(
        LEDCommand(status="ON", raspberry_id=raspberry_id, led_type=led_type), 
        db
    )

@app.post("/api/led/{led_type}/off", tags=["LED Control"])
def led_off(
    led_type: str,
    raspberry_id: int = Query(1, description="ID da Raspberry Pi"),
    db: Session = Depends(get_db)
):
    """Atalho para desligar LED (interno ou externo)"""
    return control_led(
        LEDCommand(status="OFF", raspberry_id=raspberry_id, led_type=led_type), 
        db
    )

@app.get("/api/led/status", tags=["LED Control"])
def get_led_status(
    raspberry_id: int = Query(1, description="ID da Raspberry Pi"),
    db: Session = Depends(get_db)
):
    """Retorna o status atual dos LEDs (interno e externo)"""
    device = db.query(DeviceStatus).filter(
        DeviceStatus.raspberry_id == raspberry_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=404, 
            detail="Dispositivo não encontrado"
        )
    
    return {
        "raspberry_id": raspberry_id,
        "led_internal": "ON" if device.led_internal_status else "OFF",
        "led_external": "ON" if device.led_external_status else "OFF",
        "last_update": device.last_update
    }

@app.get("/api/led/history", response_model=List[LEDHistoryResponse], tags=["LED Control"])
def get_led_history(
    raspberry_id: Optional[int] = Query(None, description="Filtrar por ID da Raspberry"),
    led_type: Optional[str] = Query(None, description="Filtrar por tipo (internal/external)"),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """Retorna histórico de acionamentos dos LEDs"""
    query = db.query(LEDHistory)
    
    if raspberry_id:
        query = query.filter(LEDHistory.raspberry_id == raspberry_id)
    if led_type:
        query = query.filter(LEDHistory.led_type == led_type)
    
    history = query.order_by(LEDHistory.timestamp.desc()).limit(limit).all()
    return history

# ============= ENDPOINTS DE STATUS DOS DISPOSITIVOS =============

@app.get("/api/devices/status", response_model=List[DeviceStatusResponse], tags=["Device Status"])
def get_all_devices_status(db: Session = Depends(get_db)):
    """Retorna status de todos os dispositivos do cluster"""
    devices = db.query(DeviceStatus).all()
    return devices

@app.get("/api/devices/{raspberry_id}/status", response_model=DeviceStatusResponse, tags=["Device Status"])
def get_device_status(raspberry_id: int, db: Session = Depends(get_db)):
    """Retorna status completo de uma Raspberry específica"""
    device = db.query(DeviceStatus).filter(
        DeviceStatus.raspberry_id == raspberry_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=404, 
            detail="Dispositivo não encontrado"
        )
    
    return device

# ============= ENDPOINTS DE DADOS EM TEMPO REAL =============

@app.get("/api/data/realtime", tags=["Real-time Data"])
def get_realtime_data(limit: int = Query(50, le=200)):
    """Retorna as últimas mensagens recebidas via RabbitMQ"""
    
    if received_messages:
        return {
            "count": len(received_messages),
            "data": received_messages[-limit:]
        }
    else:
        return {
            "count": 0,
            "data": []
        }
    
@app.post("/api/data", tags=["Real-time Data"])
def post_data(data: dict):
    """Endpoint para receber dados manualmente (para testes)"""
    received_messages.append(data)
    return {"status": "received", "data": data}

# ============= ENDPOINTS DE HEALTH CHECK =============

@app.get("/", tags=["Health Check"])
def root():
    """Endpoint raiz com informações básicas da API"""
    return {
        "status": "online",
        "service": "Raspberry Pi 5",
        "version": "2.0.0",
        "gpio_available": GPIO_AVAILABLE,
        "features": [
            "LED Control (Internal & External)",
            "Device Health Monitoring",
            "RabbitMQ Messaging",
            "Historical Data Storage"
        ]
    }

@app.get("/health", tags=["Health Check"])
def health_check(db: Session = Depends(get_db)):
    """
    Health check completo da API
    Verifica banco de dados, RabbitMQ e GPIO
    """
    health_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "gpio": "available" if GPIO_AVAILABLE else "unavailable (simulation mode)"
    }
    
    # Testar conexão com o banco
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    # Verificar consumer do RabbitMQ
    health_status["rabbitmq_consumer"] = "running"
    
    # Contar dispositivos registrados
    try:
        device_count = db.query(DeviceStatus).count()
        health_status["registered_devices"] = device_count
    except:
        health_status["registered_devices"] = "unknown"
    
    return health_status

@app.get("/api/stats", tags=["Health Check"])
def get_stats(db: Session = Depends(get_db)):
    """Retorna estatísticas gerais do sistema"""
    try:
        total_devices = db.query(DeviceStatus).count()
        total_led_actions = db.query(LEDHistory).count()
        
        # Últimas 24 horas
        since = datetime.utcnow() - timedelta(hours=24)
        recent_actions = db.query(LEDHistory).filter(
            LEDHistory.timestamp >= since
        ).count()
        
        return {
            "total_devices": total_devices,
            "total_led_actions": total_led_actions,
            "led_actions_24h": recent_actions,
            "realtime_messages": len(received_messages),
            "gpio_available": GPIO_AVAILABLE
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= EVENTO DE SHUTDOWN =============

@app.on_event("shutdown")
def shutdown_event():
    """Limpa recursos ao desligar a API"""
    print("Desligando API...")
    GPIOController.cleanup()


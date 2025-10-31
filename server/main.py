from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from consumer import start_consumer_thread
from shared import received_messages
from database import (
    get_db, init_db, LEDHistory, DeviceStatus, DeviceStatusHistory,
    RFIDTag, RFIDReadHistory, SessionLocal
)
from schemas import (
    LEDCommand, LEDHistoryResponse, DeviceStatusResponse,
    RFIDTagCreate, RFIDTagResponse, RFIDReadHistoryResponse,
    RFIDReadEvent
)
from gpio_handler import GPIOController, GPIO_AVAILABLE
from rfid_handler import init_rfid_handler, get_rfid_handler, cleanup_rfid
import csv
import io

# Inicializar banco de dados
init_db()

# Iniciar RFID handler
init_rfid_handler()
rfid_handler = get_rfid_handler()
if rfid_handler:
    # Inicia thread de polling para leitura contínua de tags
    rfid_handler.start_polling(interval=0.3)

# Iniciar consumer do RabbitMQ em thread separada
start_consumer_thread()

app = FastAPI(
    title="Raspberry Pi 5 IoT API",
    description="API para gerenciamento de cluster Raspberry Pi com controle de LEDs, RFID e health check",
    version="3.0.0"
)

# CORS amplo para permitir controle entre placas (ambiente local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==================== LED ENDPOINTS ====================

@app.post("/api/led/control", tags=["LED Control"])
def control_led(command: LEDCommand, db: Session = Depends(get_db)):
    raspberry_id = command.raspberry_id
    led_type = command.led_type.lower()
    
    if led_type not in ["internal", "external"]:
        raise HTTPException(status_code=400, detail="led_type deve ser 'internal' ou 'external'")
    
    if command.status.upper() not in ["ON", "OFF"]:
        raise HTTPException(status_code=400, detail="status deve ser 'ON' ou 'OFF'")
    
    # Usa o pino fornecido caso exista; senão, usa o padrão por tipo
    try:
        pin_to_use = int(command.pin) if command.pin is not None else GPIOController.get_pin(led_type)
    except Exception:
        raise HTTPException(status_code=400, detail="Pino inválido")

    if pin_to_use < 0 or pin_to_use > 40:
        raise HTTPException(status_code=400, detail="Pino fora do intervalo permitido")

    led_state = command.status.upper() == "ON"

    try:
        success = GPIOController.set_led(pin_to_use, led_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no GPIO: {str(e)}")

    if not success:
        raise HTTPException(status_code=500, detail="Erro ao controlar LED (GPIO retornou falso)")
    
    device = db.query(DeviceStatus).filter(DeviceStatus.raspberry_id == raspberry_id).first()
    
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
    
    history = LEDHistory(
        raspberry_id=raspberry_id,
        led_type=led_type,
        pin=pin_to_use,
        action=command.status.upper()
    )
    
    db.add(history)
    db.commit()

    # Salvar snapshot contínuo do status do dispositivo
    try:
        if device:
            snapshot = DeviceStatusHistory(
                raspberry_id=device.raspberry_id,
                led_internal_status=device.led_internal_status,
                led_external_status=device.led_external_status,
                wifi_status=device.wifi_status,
                mem_usage=device.mem_usage,
                cpu_temp=device.cpu_temp,
                cpu_percent=device.cpu_percent,
                gpio_used_count=device.gpio_used_count,
                spi_buses=device.spi_buses,
                i2c_buses=device.i2c_buses,
                usb_devices_count=device.usb_devices_count,
                net_bytes_sent=device.net_bytes_sent,
                net_bytes_recv=device.net_bytes_recv,
                net_ifaces=device.net_ifaces,
                rfid_reader_status=device.rfid_reader_status,
                last_rfid_read=device.last_rfid_read
            )
            db.add(snapshot)
            db.commit()
    except Exception as e:
        print(f"[DeviceHistory] Falha ao salvar snapshot: {e}")
    
    return {
        "message": f"LED {led_type} {'ligado' if led_state else 'desligado'}",
        "raspberry_id": raspberry_id,
        "led_type": led_type,
        "pin": pin_to_use,
        "status": command.status.upper(),
        "gpio_available": GPIO_AVAILABLE,
        "timestamp": datetime.utcnow()
    }

@app.post("/api/led/{led_type}/on", tags=["LED Control"])
def led_on(
    led_type: str,
    raspberry_id: str = Query("1", description="ID da Raspberry Pi"),
    pin: Optional[int] = Query(None, description="Número do pino GPIO (BCM) a ser usado"),
    db: Session = Depends(get_db)
):
    return control_led(LEDCommand(status="ON", raspberry_id=raspberry_id, led_type=led_type, pin=pin), db)

@app.post("/api/led/{led_type}/off", tags=["LED Control"])
def led_off(
    led_type: str,
    raspberry_id: str = Query("1", description="ID da Raspberry Pi"),
    pin: Optional[int] = Query(None, description="Número do pino GPIO (BCM) a ser usado"),
    db: Session = Depends(get_db)
):
    return control_led(LEDCommand(status="OFF", raspberry_id=raspberry_id, led_type=led_type, pin=pin), db)

@app.get("/api/led/status", tags=["LED Control"])
def get_led_status(
    raspberry_id: str = Query("1", description="ID da Raspberry Pi"),
    db: Session = Depends(get_db)
):
    device = db.query(DeviceStatus).filter(DeviceStatus.raspberry_id == raspberry_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    return {
        "raspberry_id": raspberry_id,
        "led_internal": "ON" if device.led_internal_status else "OFF",
        "led_external": "ON" if device.led_external_status else "OFF",
        "last_update": device.last_update
    }

@app.get("/api/led/history", response_model=List[LEDHistoryResponse], tags=["LED Control"])
def get_led_history(
    raspberry_id: Optional[str] = Query(None, description="Filtrar por ID da Raspberry"),
    led_type: Optional[str] = Query(None, description="Filtrar por tipo (internal/external)"),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(LEDHistory)
    
    if raspberry_id:
        query = query.filter(LEDHistory.raspberry_id == raspberry_id)
    if led_type:
        query = query.filter(LEDHistory.led_type == led_type)
    
    history = query.order_by(LEDHistory.timestamp.desc()).limit(limit).all()
    return history

# ==================== RFID ENDPOINTS ====================

@app.post("/api/rfid/read", tags=["RFID"])
def receive_rfid_read(read_event: RFIDReadEvent, db: Session = Depends(get_db)):
    """
    Recebe evento de leitura RFID.
    Pode ser chamado pelo hardware da Raspberry ou usado para testes.
    """
    try:
        # Logar no terminal a leitura recebida
        print(f"[RFID] Evento recebido UID={read_event.uid} Nome={read_event.tag_name} Raspberry={read_event.raspberry_id}")
        # Salvar ou atualizar tag no banco
        tag = db.query(RFIDTag).filter(RFIDTag.uid == read_event.uid).first()
        if not tag:
            tag = RFIDTag(
                uid=read_event.uid,
                name=read_event.tag_name or "<Sem nome>",
                raspberry_id=read_event.raspberry_id
            )
            db.add(tag)
        
        # Registrar no histórico de leituras
        read_history = RFIDReadHistory(
            uid=read_event.uid,
            tag_name=read_event.tag_name or "<Sem nome>",
            raspberry_id=read_event.raspberry_id,
            timestamp=read_event.timestamp or datetime.utcnow()
        )
        db.add(read_history)
        
        # Atualizar status do dispositivo
        device = db.query(DeviceStatus).filter(
            DeviceStatus.raspberry_id == read_event.raspberry_id
        ).first()
        if device:
            device.last_rfid_read = datetime.utcnow()
            device.rfid_reader_status = "online"
        else:
            device = DeviceStatus(
                raspberry_id=read_event.raspberry_id,
                rfid_reader_status="online",
                last_rfid_read=datetime.utcnow()
            )
            db.add(device)
        
        db.commit()

        # Snapshot contínuo do status do dispositivo
        try:
            device_snapshot_source = db.query(DeviceStatus).filter(
                DeviceStatus.raspberry_id == read_event.raspberry_id
            ).first()
            if device_snapshot_source:
                snapshot = DeviceStatusHistory(
                    raspberry_id=device_snapshot_source.raspberry_id,
                    led_internal_status=device_snapshot_source.led_internal_status,
                    led_external_status=device_snapshot_source.led_external_status,
                    wifi_status=device_snapshot_source.wifi_status,
                    mem_usage=device_snapshot_source.mem_usage,
                    cpu_temp=device_snapshot_source.cpu_temp,
                    cpu_percent=device_snapshot_source.cpu_percent,
                    gpio_used_count=device_snapshot_source.gpio_used_count,
                    spi_buses=device_snapshot_source.spi_buses,
                    i2c_buses=device_snapshot_source.i2c_buses,
                    usb_devices_count=device_snapshot_source.usb_devices_count,
                    net_bytes_sent=device_snapshot_source.net_bytes_sent,
                    net_bytes_recv=device_snapshot_source.net_bytes_recv,
                    net_ifaces=device_snapshot_source.net_ifaces,
                    rfid_reader_status=device_snapshot_source.rfid_reader_status,
                    last_rfid_read=device_snapshot_source.last_rfid_read
                )
                db.add(snapshot)
                db.commit()
        except Exception as e:
            print(f"[DeviceHistory] Snapshot após RFID falhou: {e}")
        
        return {
            "status": "success",
            "message": f"Tag {read_event.uid} lida com sucesso",
            "tag_name": read_event.tag_name,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao processar leitura: {str(e)}")

@app.post("/api/rfid/tag", response_model=RFIDTagResponse, tags=["RFID"])
def create_or_update_rfid_tag(tag_data: RFIDTagCreate, db: Session = Depends(get_db)):
    """Cria ou atualiza um nome para uma tag RFID"""
    try:
        tag = db.query(RFIDTag).filter(RFIDTag.uid == tag_data.uid).first()
        
        if tag:
            tag.name = tag_data.name
            tag.updated_at = datetime.utcnow()
        else:
            tag = RFIDTag(
                uid=tag_data.uid,
                name=tag_data.name,
                raspberry_id=tag_data.raspberry_id
            )
            db.add(tag)
        
        db.commit()
        db.refresh(tag)
        
        return tag
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar tag: {str(e)}")

@app.get("/api/rfid/tags", response_model=List[RFIDTagResponse], tags=["RFID"])
def list_rfid_tags(
    raspberry_id: Optional[str] = Query(None, description="Filtrar por Raspberry ID"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Lista todas as tags RFID cadastradas"""
    query = db.query(RFIDTag)
    
    if raspberry_id:
        query = query.filter(RFIDTag.raspberry_id == raspberry_id)
    
    tags = query.order_by(RFIDTag.created_at.desc()).limit(limit).all()
    return tags

@app.get("/api/rfid/tag/{uid}", response_model=RFIDTagResponse, tags=["RFID"])
def get_rfid_tag(uid: str, db: Session = Depends(get_db)):
    """Obtém informações de uma tag RFID específica"""
    tag = db.query(RFIDTag).filter(RFIDTag.uid == uid).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    
    return tag

@app.delete("/api/rfid/tag/{uid}", tags=["RFID"])
def delete_rfid_tag(uid: str, db: Session = Depends(get_db)):
    """Deleta uma tag RFID"""
    tag = db.query(RFIDTag).filter(RFIDTag.uid == uid).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    
    db.delete(tag)
    db.commit()
    
    return {"message": f"Tag {uid} deletada com sucesso"}

@app.get("/api/rfid/history", response_model=List[RFIDReadHistoryResponse], tags=["RFID"])
def get_rfid_read_history(
    raspberry_id: Optional[str] = Query(None, description="Filtrar por Raspberry ID"),
    uid: Optional[str] = Query(None, description="Filtrar por UID da tag"),
    hours: int = Query(24, description="Histórico das últimas N horas"),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Obtém histórico de leituras RFID"""
    query = db.query(RFIDReadHistory)
    
    # Filtrar por data
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(RFIDReadHistory.timestamp >= since)
    
    if raspberry_id:
        query = query.filter(RFIDReadHistory.raspberry_id == raspberry_id)
    
    if uid:
        query = query.filter(RFIDReadHistory.uid == uid)
    
    history = query.order_by(RFIDReadHistory.timestamp.desc()).limit(limit).all()
    return history

@app.get("/api/rfid/last", tags=["RFID"])
def get_last_rfid_read(
    raspberry_id: str = Query(..., description="Raspberry ID"),
    db: Session = Depends(get_db)
):
    """Retorna a última leitura RFID para a Raspberry especificada"""
    record = db.query(RFIDReadHistory).filter(
        RFIDReadHistory.raspberry_id == raspberry_id
    ).order_by(RFIDReadHistory.timestamp.desc()).first()
    if not record:
        return {"exists": False}
    return {
        "exists": True,
        "uid": record.uid,
        "tag_name": record.tag_name,
        "raspberry_id": record.raspberry_id,
        "timestamp": record.timestamp
    }

@app.get("/api/rfid/history.csv", tags=["RFID"])
def export_rfid_history_csv(
    raspberry_id: Optional[str] = Query(None),
    hours: int = Query(24),
    db: Session = Depends(get_db)
):
    """Exporta o histórico de leituras RFID em CSV"""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(RFIDReadHistory).filter(RFIDReadHistory.timestamp >= since)
    if raspberry_id:
        query = query.filter(RFIDReadHistory.raspberry_id == raspberry_id)
    rows = query.order_by(RFIDReadHistory.timestamp.desc()).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp", "raspberry_id", "uid", "tag_name"]) 
    for r in rows:
        writer.writerow([r.timestamp.isoformat(), r.raspberry_id, r.uid, r.tag_name])
    buffer.seek(0)

    filename = "rfid_history.csv"
    return StreamingResponse(iter([buffer.read()]), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

@app.get("/api/rfid/stats", tags=["RFID"])
def get_rfid_stats(
    raspberry_id: Optional[str] = Query(None),
    hours: int = Query(24),
    db: Session = Depends(get_db)
):
    """Obtém estatísticas de leitura RFID"""
    query = db.query(RFIDReadHistory)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(RFIDReadHistory.timestamp >= since)
    
    if raspberry_id:
        query = query.filter(RFIDReadHistory.raspberry_id == raspberry_id)
    
    total_reads = query.count()
    
    # Contar reads únicos
    unique_tags = db.session.query(RFIDReadHistory.uid).filter(
        RFIDReadHistory.timestamp >= since
    ).distinct().count()
    
    return {
        "total_reads": total_reads,
        "unique_tags_read": unique_tags,
        "period_hours": hours,
        "timestamp": datetime.utcnow()
    }

# ==================== DEVICE STATUS ENDPOINTS ====================

@app.get("/api/devices/status", response_model=List[DeviceStatusResponse], tags=["Device Status"])
def get_all_devices_status(db: Session = Depends(get_db)):
    devices = db.query(DeviceStatus).all()
    return [DeviceStatusResponse.from_orm(device) for device in devices]

@app.get("/api/devices/{raspberry_id}/status", response_model=DeviceStatusResponse, tags=["Device Status"])
def get_device_status(raspberry_id: str, db: Session = Depends(get_db)):
    device = db.query(DeviceStatus).filter(DeviceStatus.raspberry_id == raspberry_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    
    return DeviceStatusResponse.from_orm(device)

@app.get("/api/devices/{raspberry_id}/status/history", response_model=List[DeviceStatusHistoryResponse], tags=["Device Status"])
def get_device_status_history(
    raspberry_id: str,
    hours: int = Query(24, le=720),
    limit: int = Query(500, le=5000),
    db: Session = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = db.query(DeviceStatusHistory).filter(
        DeviceStatusHistory.raspberry_id == raspberry_id,
        DeviceStatusHistory.timestamp >= since
    ).order_by(DeviceStatusHistory.timestamp.desc()).limit(limit).all()
    return rows

# ==================== REAL-TIME DATA ENDPOINTS ====================

@app.get("/api/data/realtime", tags=["Real-time Data"])
def get_realtime_data(limit: int = Query(50, le=200)):
    if received_messages:
        return {
            "count": len(received_messages),
            "data": received_messages[-limit:]
        }
    
    return {
        "count": 0,
        "data": []
    }

@app.post("/api/data", tags=["Real-time Data"])
def post_data(data: dict):
    received_messages.append(data)
    return {"status": "received", "data": data}

# ==================== HEALTH CHECK ENDPOINTS ====================

@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "service": "Raspberry Pi 5 IoT",
        "version": "3.0.0",
        "gpio_available": GPIO_AVAILABLE,
        "features": [
            "LED Control (Internal & External)",
            "RFID Tag Reading & Management",
            "Device Health Monitoring",
            "RabbitMQ Messaging",
            "Historical Data Storage"
        ]
    }

@app.get("/health", tags=["Health Check"])
def health_check(db: Session = Depends(get_db)):
    health_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "gpio": "available" if GPIO_AVAILABLE else "unavailable (simulation mode)"
    }
    
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    health_status["rabbitmq_consumer"] = "running"
    
    # Verificar RFID handler
    rfid_handler = get_rfid_handler()
    health_status["rfid"] = "available" if rfid_handler else "unavailable"
    
    try:
        device_count = db.query(DeviceStatus).count()
        health_status["registered_devices"] = device_count
    except:
        health_status["registered_devices"] = "unknown"
    
    return health_status

@app.get("/api/stats", tags=["Health Check"])
def get_stats(db: Session = Depends(get_db)):
    try:
        total_devices = db.query(DeviceStatus).count()
        total_led_actions = db.query(LEDHistory).count()
        total_rfid_reads = db.query(RFIDReadHistory).count()
        total_rfid_tags = db.query(RFIDTag).count()
        
        since = datetime.utcnow() - timedelta(hours=24)
        recent_actions = db.query(LEDHistory).filter(LEDHistory.timestamp >= since).count()
        recent_rfid_reads = db.query(RFIDReadHistory).filter(RFIDReadHistory.timestamp >= since).count()
        
        return {
            "total_devices": total_devices,
            "total_led_actions": total_led_actions,
            "led_actions_24h": recent_actions,
            "total_rfid_tags": total_rfid_tags,
            "total_rfid_reads": total_rfid_reads,
            "rfid_reads_24h": recent_rfid_reads,
            "realtime_messages": len(received_messages),
            "gpio_available": GPIO_AVAILABLE,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    print("Desligando API...")
    GPIOController.cleanup()
    cleanup_rfid()




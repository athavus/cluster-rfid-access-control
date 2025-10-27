import pika
import json
import threading
from shared import received_messages
from database import SessionLocal, DeviceStatus
from datetime import datetime

def process_raspberry_data(data):
    """Processa dados de health check das Raspberries e salva no banco"""
    db = SessionLocal()
    try:
        raspberry_id = data.get("id")
        
        # Atualizar status do dispositivo
        device = db.query(DeviceStatus).filter(
            DeviceStatus.raspberry_id == raspberry_id
        ).first()
        
        if device:
            device.wifi_status = data.get("wifi_status", device.wifi_status)
            device.mem_usage = data.get("mem_usage", device.mem_usage)
            device.cpu_temp = data.get("cpu_temp", device.cpu_temp)
            device.last_update = datetime.utcnow()
        else:
            device = DeviceStatus(
                raspberry_id=raspberry_id,
                wifi_status=data.get("wifi_status", "unknown"),
                mem_usage=data.get("mem_usage", "0 MB"),
                cpu_temp=data.get("cpu_temp", "0°C"),
                led_internal_status=False,
                led_external_status=False
            )
            db.add(device)
        
        db.commit()
        print(f"Status atualizado para Raspberry {raspberry_id}")
        
    except Exception as e:
        print(f"Erro ao processar dados: {e}")
        db.rollback()
    finally:
        db.close()

def rabbit_consumer():
    """Consumer do RabbitMQ que processa mensagens das Raspberries"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost', heartbeat=600)
        )
        channel = connection.channel()
        channel.queue_declare(queue='rasp_data', durable=True)

        def callback(ch, method, properties, body):
            try:
                data = json.loads(body)
                print(f"Recebido: {data}")
                received_messages.append(data)
                
                # Processar e salvar no banco de dados
                process_raspberry_data(data)
                
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {e}")
            except Exception as e:
                print(f"Erro no callback: {e}")

        channel.basic_consume(
            queue='rasp_data', 
            on_message_callback=callback, 
            auto_ack=True
        )
        
        print("RabbitMQ consumer iniciado")
        channel.start_consuming()
        
    except Exception as e:
        print(f"Erro ao conectar no RabbitMQ: {e}")

def start_consumer_thread():
    """Inicia o consumer em uma thread separada"""
    t = threading.Thread(target=rabbit_consumer, daemon=True)
    t.start()
    print("Thread do consumer iniciada")


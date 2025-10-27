import pika
import json
import time
import psutil  # pip install psutil

def get_system_info():
    """Coleta informações do sistema"""
    try:
        # Uso de memória
        mem = psutil.virtual_memory()
        mem_usage = f"{int(mem.used / (1024**2))} MB"
        
        # Temperatura da CPU (funciona na Raspberry Pi)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000.0
                cpu_temp = f"{temp:.1f}°C"
        except:
            cpu_temp = "N/A"
        
        # Status do WiFi (simplificado)
        wifi_status = "online" if psutil.net_if_stats().get("wlan0") else "unknown"
        
        return mem_usage, cpu_temp, wifi_status
    except:
        return "N/A", "N/A", "unknown"

def publish_health_data():
    """
    Publica dados de health check das Raspberries
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost', heartbeat=600)
        )
        channel = connection.channel()
        channel.queue_declare(queue='rasp_data', durable=True)
        
        cont_messages = 0
        raspberry_id = 1  # Altere conforme necessário
        
        print(f"Iniciando publicação de health check para Raspberry {raspberry_id}")
        print("Pressione CTRL+C para parar\n")

        while True:
            try:
                # Coletar dados do sistema
                mem_usage, cpu_temp, wifi_status = get_system_info()
                
                data = {
                    "id": raspberry_id,
                    "mem_usage": mem_usage,
                    "cpu_temp": cpu_temp,
                    "wifi_status": wifi_status,
                    "timestamp": time.time()
                }
                
                channel.basic_publish(
                    exchange='', 
                    routing_key='rasp_data', 
                    body=json.dumps(data),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Mensagem persistente
                    )
                )
                
                print(f"[{time.strftime('%H:%M:%S')}] Rasp {raspberry_id}: "
                      f"Mem={mem_usage}, Temp={cpu_temp}, WiFi={wifi_status}")
                
                cont_messages += 1
                time.sleep(5)  # Enviar a cada 5 segundos
                
            except KeyboardInterrupt:
                print("\nParando publicador...")
                break
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(5)
        
        connection.close()
        return cont_messages
        
    except Exception as e:
        print(f"Erro ao conectar no RabbitMQ: {e}")
        return 0

if __name__ == "__main__":
    cont_messages = publish_health_data()
    print(f"\nTotal de mensagens enviadas: {cont_messages}")


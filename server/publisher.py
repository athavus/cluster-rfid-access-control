import pika
import json
import time
import psutil  # pip install psutil
import os
from glob import glob
import socket  # para hostname único

def get_system_info():
    """Coleta informações do sistema ampliadas"""
    try:
        mem = psutil.virtual_memory()
        mem_usage = f"{int(mem.used / (1024**2))} MB"
        cpu_percent = psutil.cpu_percent(interval=0)

        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000.0
                cpu_temp = f"{temp:.1f}°C"
        except:
            cpu_temp = "N/A"

        wifi_status = "online" if psutil.net_if_stats().get("wlan0") else "unknown"

        spi_buses = len(glob('/dev/spidev*'))
        i2c_buses = len(glob('/dev/i2c-*'))

        usb_devices_count = len(glob('/sys/bus/usb/devices/*usb*'))

        net_io = psutil.net_io_counters()
        net_bytes_sent = net_io.bytes_sent
        net_bytes_recv = net_io.bytes_recv

        net_ifaces = [iface for iface, addrs in psutil.net_if_addrs().items() if psutil.net_if_stats()[iface].isup]

        gpio_used_count = 0

        return {
            "mem_usage": mem_usage,
            "cpu_temp": cpu_temp,
            "wifi_status": wifi_status,
            "cpu_percent": cpu_percent,
            "gpio_used_count": gpio_used_count,
            "spi_buses": spi_buses,
            "i2c_buses": i2c_buses,
            "usb_devices_count": usb_devices_count,
            "net_bytes_sent": net_bytes_sent,
            "net_bytes_recv": net_bytes_recv,
            "net_ifaces": net_ifaces
        }

    except Exception as e:
        print(f"Erro ao coletar info do sistema: {e}")
        return {
            "mem_usage": "N/A",
            "cpu_temp": "N/A",
            "wifi_status": "unknown",
            "cpu_percent": 0,
            "gpio_used_count": 0,
            "spi_buses": 0,
            "i2c_buses": 0,
            "usb_devices_count": 0,
            "net_bytes_sent": 0,
            "net_bytes_recv": 0,
            "net_ifaces": []
        }

def publish_health_data():
    try:
        credentials = pika.PlainCredentials('athavus', '1234')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('192.168.130.9', 5672, '/', credentials, heartbeat=600)
        )
        channel = connection.channel()
        channel.queue_declare(queue='rasp_data', durable=True)

        cont_messages = 0
        raspberry_id = socket.gethostname()  # ID dinâmico pelo hostname

        print(f"Iniciando publicação ampliada de health check para Raspberry {raspberry_id}")
        print("Pressione CTRL+C para parar\n")

        while True:
            try:
                sys_info = get_system_info()

                data = {
                    "id": raspberry_id,
                    **sys_info,
                    "timestamp": time.time()
                }

                channel.basic_publish(
                    exchange='',
                    routing_key='rasp_data',
                    body=json.dumps(data),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                    )
                )

                print(f"[{time.strftime('%H:%M:%S')}] Rasp {raspberry_id}: {data}")

                cont_messages += 1
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nParando publicador...")
                break
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(1)

        connection.close()
        return cont_messages

    except Exception as e:
        print(f"Erro ao conectar no RabbitMQ: {e}")
        return 0

if __name__ == "__main__":
    cont_messages = publish_health_data()
    print(f"\nTotal de mensagens enviadas: {cont_messages}")


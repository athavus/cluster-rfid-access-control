import pika
import json
import time
import random

def publish_fake_data():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='rasp_data')
    cont_messages = 0

    while True:
        try:        
            data = {
                "id": random.randint(1, 100),
                "mem_usage": f"{random.randint(100, 700)} MB",
                "wifi_status": random.choice(["online", "offline"]),
                "timestamp": time.time()
            }
            channel.basic_publish(exchange='', routing_key='rasp_data', body=json.dumps(data))
            print(f"Sent: {data}")
            cont_messages += 1
            time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"Foram enviadas: {cont_messages} mensagens")

if __name__ == "__main__":
    publish_fake_data()

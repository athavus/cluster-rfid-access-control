import pika
import json
import threading
from shared import received_messages

def rabbit_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='rasp_data')

    def callback(ch, method, properties, body):
        data = json.loads(body)
        print(f"Received: {data}")
        received_messages.append(data)

    channel.basic_consume(queue='rasp_data', on_message_callback=callback, auto_ack=True)
    print("RabbitMQ consumer started")
    channel.start_consuming()

def start_consumer_thread():
    t = threading.Thread(target=rabbit_consumer, daemon=True)
    t.start()

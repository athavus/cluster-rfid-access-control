from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from consumer import start_consumer_thread
from shared import received_messages
import RPi.GPIO as GPIO

start_consumer_thread()

app = FastAPI()
LED_PIN = 18
origins = ["http://localhost:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/data")
async def get_data():
    return received_messages

@app.post("/api/data")
async def post_data(data: dict):
    received_messages.append(data)
    return {"status": "received"}

# ENDPOINTS PARA FAZER O CONTROLE DOS LEDS.
@app.post("/led/on")
def led_on():
    GPIO.output(LED_PIN, GPIO.HIGH)
    return { "message": "LED LIGADO" }

@app.post("/led/off")
def led_off():
    GPIO.output(LED_PIN, GPIO.LOW)
    return { "message" : "LED DESLIGADO" }

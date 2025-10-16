from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from consumer import start_consumer_thread
from shared import received_messages

start_consumer_thread()

app = FastAPI()

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

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./raspberry_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LEDHistory(Base):
    __tablename__ = "led_history"

    id = Column(Integer, primary_key=True, index=True)
    raspberry_id = Column(String, index=True)  # agora string
    led_type = Column(String)
    pin = Column(Integer)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class DeviceStatus(Base):
    __tablename__ = "device_status"

    id = Column(Integer, primary_key=True, index=True)
    raspberry_id = Column(String, unique=True, index=True)  # string para o hostname
    led_internal_status = Column(Boolean, default=False)
    led_external_status = Column(Boolean, default=False)
    wifi_status = Column(String, default="unknown")
    mem_usage = Column(String, default="0 MB")
    cpu_temp = Column(String, default="0°C")
    cpu_percent = Column(Float, default=0.0)
    gpio_used_count = Column(Integer, default=0)
    spi_buses = Column(Integer, default=0)
    i2c_buses = Column(Integer, default=0)
    usb_devices_count = Column(Integer, default=0)
    net_bytes_sent = Column(Integer, default=0)
    net_bytes_recv = Column(Integer, default=0)
    net_ifaces = Column(Text, default="[]")
    last_update = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


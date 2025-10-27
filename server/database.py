from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Configuração do banco SQLite
DATABASE_URL = "sqlite:///./raspberry_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo para histórico de acionamentos de LEDs
class LEDHistory(Base):
    __tablename__ = "led_history"
    
    id = Column(Integer, primary_key=True, index=True)
    raspberry_id = Column(Integer, index=True)
    led_type = Column(String)  # "internal" ou "external"
    pin = Column(Integer)
    action = Column(String)  # "ON" ou "OFF"
    timestamp = Column(DateTime, default=datetime.utcnow)

# Modelo para status dos dispositivos
class DeviceStatus(Base):
    __tablename__ = "device_status"
    
    id = Column(Integer, primary_key=True, index=True)
    raspberry_id = Column(Integer, unique=True, index=True)
    led_internal_status = Column(Boolean, default=False)
    led_external_status = Column(Boolean, default=False)
    wifi_status = Column(String, default="unknown")
    mem_usage = Column(String, default="0 MB")
    cpu_temp = Column(String, default="0°C")
    last_update = Column(DateTime, default=datetime.utcnow)

# Criar todas as tabelas
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


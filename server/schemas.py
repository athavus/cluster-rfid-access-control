from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LEDCommand(BaseModel):
    status: str  # "ON" ou "OFF"
    raspberry_id: Optional[int] = 1
    led_type: Optional[str] = "external"  # "internal" ou "external"

class LEDHistoryResponse(BaseModel):
    id: int
    raspberry_id: int
    led_type: str
    pin: int
    action: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class DeviceStatusResponse(BaseModel):
    raspberry_id: int
    led_internal_status: bool
    led_external_status: bool
    wifi_status: str
    mem_usage: str
    cpu_temp: str
    last_update: datetime
    
    class Config:
        from_attributes = True

class RaspberryMessage(BaseModel):
    id: int
    mem_usage: Optional[str] = None
    wifi_status: Optional[str] = None
    cpu_temp: Optional[str] = None
    timestamp: float


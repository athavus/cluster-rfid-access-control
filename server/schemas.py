from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import json

class LEDCommand(BaseModel):
    status: str
    raspberry_id: Optional[str] = "1"  # agora string
    led_type: Optional[str] = "external"

class LEDHistoryResponse(BaseModel):
    id: int
    raspberry_id: str  # string
    led_type: str
    pin: int
    action: str
    timestamp: datetime

    class Config:
        from_attributes = True

class DeviceStatusResponse(BaseModel):
    raspberry_id: str
    led_internal_status: bool
    led_external_status: bool
    wifi_status: str
    mem_usage: str
    cpu_temp: str
    cpu_percent: float
    gpio_used_count: int
    spi_buses: int
    i2c_buses: int
    usb_devices_count: int
    net_bytes_sent: int
    net_bytes_recv: int
    net_ifaces: List[str]
    last_update: datetime

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        data = obj.__dict__.copy()
        data['net_ifaces'] = json.loads(data.get('net_ifaces', '[]'))
        return cls(**data)


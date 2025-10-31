from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import json

class LEDCommand(BaseModel):
    status: str
    raspberry_id: Optional[str] = "1"
    led_type: Optional[str] = "external"
    pin: Optional[int] = None

class LEDHistoryResponse(BaseModel):
    id: int
    raspberry_id: str
    led_type: str
    pin: int
    action: str
    timestamp: datetime

    class Config:
        from_attributes = True

class RFIDTagCreate(BaseModel):
    """Schema para criar/atualizar tag RFID"""
    uid: str
    name: str
    raspberry_id: Optional[str] = "1"

class RFIDTagResponse(BaseModel):
    """Schema para resposta de tag RFID"""
    id: int
    uid: str
    name: str
    raspberry_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RFIDReadHistoryResponse(BaseModel):
    """Schema para histórico de leituras RFID"""
    id: int
    uid: str
    tag_name: str
    raspberry_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class RFIDReadEvent(BaseModel):
    """Schema para evento de leitura RFID (recebido do hardware)"""
    uid: str
    tag_name: Optional[str] = "<Sem nome>"
    raspberry_id: Optional[str] = "1"
    timestamp: Optional[datetime] = None

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
    rfid_reader_status: str
    last_rfid_read: Optional[datetime]
    last_update: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        data = obj.__dict__.copy()
        data['net_ifaces'] = json.loads(data.get('net_ifaces', '[]'))
        return cls(**data)


class DeviceStatusHistoryResponse(BaseModel):
    id: int
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
    rfid_reader_status: str
    last_rfid_read: Optional[datetime]
    timestamp: datetime

    class Config:
        from_attributes = True



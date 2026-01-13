# API Reference

O sistema expõe duas interfaces de comunicação:
1.  **RabbitMQ Messages**: Para comunicação assíncrona entre Raspberries e Servidor.
2.  **HTTP REST API**: Para o Frontend (Client) e integrações externas.

## 1. RabbitMQ (Async)

**Queue**: `rasp_data`
**Publisher**: Raspberries (Edge Node)
**Consumer**: Server

### Payload (Health Check)
Enviado a cada 1 segundo (configurável) pelas Raspberries.

```json
{
  "id": "raspberrypi",
  "mem_usage": "512 MB",
  "cpu_temp": "48.1°C",
  "wifi_status": "MyWifiSSID",
  "cpu_percent": 7.5,
  "gpio_used_count": 0,
  "spi_buses": 1,
  "i2c_buses": 1,
  "usb_devices_count": 3,
  "net_bytes_sent": 102400,
  "net_bytes_recv": 204800,
  "net_ifaces": ["wlan0", "eth0"],
  "timestamp": 1730264823.62
}
```

---

## 2. HTTP REST API

**Base URL**: `http://<server-ip>:8000`

### Health & Status

#### `GET /`
Retorna status da API e versões.
```json
{
  "status": "online",
  "service": "Raspberry Pi 5 IoT",
  "version": "3.0.0"
}
```

#### `GET /api/devices/status`
Retorna lista de todas as Raspberries monitoradas e seu status atual.

### Controle de LEDs

#### `POST /api/led/control`
Liga ou desliga LEDs remotamente.

**Body**:
```json
{
  "raspberry_id": "raspberrypi",
  "led_type": "internal", 
  "status": "ON",
  "pin": 4
}
```
*`led_type` pode ser "internal" ou "external".*

### RFID

#### `GET /api/rfid/history`
Obtém log de leituras RFID.
**Query Params**:
- `limit`: N últimos registros (default 50)
- `raspberry_id`: Filtra por nó
- `uid`: Filtra por tag específica

#### `POST /api/rfid/tag`
Cadastra ou atualiza nome de uma Tag.
**Body**:
```json
{
  "uid": "A1:B2:C3:D4",
  "name": "Admin",
  "raspberry_id": "raspberrypi"
}
```

### Servo / Porta

#### `POST /api/servo/open`
Força a abertura da porta temporariamente.
**Body**:
```json
{
  "action": "open",
  "raspberry_id": "raspberrypi",
  "hold_time": 5.0
}
```

## Exportação de Dados

#### `GET /api/export/db.zip`
Baixa um ZIP contendo tabelas do banco em formato CSV (backup/análise).
# Camada de Persistência (SQLite + SQLAlchemy) para Monitoramento de Raspberries

Este módulo define o schema do banco, a engine, a factory de sessões e utilitários para inicialização do banco de dados. Ele centraliza o armazenamento de:
- Status e métricas das Raspberries (health check)
- Histórico de ações de LEDs
- Cadastro de tags RFID
- Histórico de leituras RFID

Feito para funcionar de forma simples com SQLite por padrão, mas facilmente adaptável para PostgreSQL/MySQL.

## Objetivos

- Persistir dados operacionais e históricos de dispositivos distribuídos.
- Fornecer um modelo único para integração com consumidores RabbitMQ e APIs web.
- Manter índices essenciais (e unicidade) para consultas rápidas.

## Visão geral da arquitetura

- Banco padrão: `sqlite:///./raspberry_data.db`
- Sessões por requisição (pattern do `get_db` gera/fecha automaticamente).
- `init_db()` cria as tabelas conforme os modelos.

## Modelos e campos

### DeviceStatus
Registro atual do dispositivo (um por Raspberry).

| Campo              | Tipo     | Detalhes/Default                         |
|--------------------|----------|------------------------------------------|
| id                 | Integer  | PK, index                                |
| raspberry_id       | String   | Único, index                             |
| led_internal_status| Boolean  | default=False                            |
| led_external_status| Boolean  | default=False                            |
| wifi_status        | String   | default="unknown"                        |
| mem_usage          | String   | default="0 MB"                           |
| cpu_temp           | String   | default="0°C"                            |
| cpu_percent        | Float    | default=0.0                              |
| gpio_used_count    | Integer  | default=0                                |
| spi_buses          | Integer  | default=0                                |
| i2c_buses          | Integer  | default=0                                |
| usb_devices_count  | Integer  | default=0                                |
| net_bytes_sent     | Integer  | default=0                                |
| net_bytes_recv     | Integer  | default=0                                |
| net_ifaces         | Text     | default="[]" (JSON string)               |
| rfid_reader_status | String   | default="offline"                        |
| last_rfid_read     | DateTime | nullable=True                            |
| last_update        | DateTime | default=datetime.utcnow                  |

Observação: `net_ifaces` armazena uma string JSON. Ao ler/gravar, use `json.loads`/`json.dumps`.

### LEDHistory
Histórico de ações nos LEDs.

| Campo        | Tipo     | Detalhes/Default          |
|--------------|----------|---------------------------|
| id           | Integer  | PK, index                 |
| raspberry_id | String   | index                     |
| led_type     | String   | ex.: "internal"/"external"|
| pin          | Integer  | pino físico               |
| action       | String   | ex.: "on", "off", "blink" |
| timestamp    | DateTime | default=datetime.utcnow   |

### RFIDTag
Cadastro das tags RFID.

| Campo        | Tipo     | Detalhes/Default          |
|--------------|----------|---------------------------|
| id           | Integer  | PK, index                 |
| uid          | String   | Único, index              |
| name         | String   | default="<Sem nome>"      |
| raspberry_id | String   | index                     |
| created_at   | DateTime | default=datetime.utcnow   |
| updated_at   | DateTime | default=datetime.utcnow (auto-update) |

### RFIDReadHistory
Histórico de leituras RFID.

| Campo        | Tipo     | Detalhes/Default                |
|--------------|----------|---------------------------------|
| id           | Integer  | PK, index                       |
| uid          | String   | index                           |
| tag_name     | String   | default="<Sem nome>"            |
| raspberry_id | String   | index                           |
| timestamp    | DateTime | default=datetime.utcnow, index  |

## Pré-requisitos

- Python 3.9+
- SQLAlchemy
- (Opcional) Driver do seu banco se não usar SQLite (ex.: psycopg2-binary)

Instalação:
```bash
pip install SQLAlchemy
# Para PostgreSQL:
# pip install psycopg2-binary
```

## Inicialização do banco

Crie as tabelas no arquivo SQLite local:
```bash
python -c "from database import init_db; init_db(); print('Tabelas criadas.')"
```

Ou no código da sua aplicação:
```python
from database import init_db
init_db()
```

O arquivo `raspberry_data.db` será criado na raiz do projeto.

## Uso de sessão (SessionLocal) e ciclo de vida

Este módulo expõe:
- `SessionLocal`: factory de sessões
- `get_db()`: gerador que abre e fecha a sessão automaticamente (útil em frameworks web)

Exemplo com context manager:
```python
from database import SessionLocal

with SessionLocal() as db:
    # use db aqui
    db.commit()
```

Exemplo com `get_db()` (padrão FastAPI-like):
```python
from database import get_db

def handler():
    for db in get_db():
        # use db
        db.commit()
```

## Exemplos práticos

- Upsert de DeviceStatus (status da Raspberry):
```python
import json
from datetime import datetime
from database import SessionLocal, DeviceStatus

payload = {
    "raspberry_id": "raspberry-01",
    "wifi_status": "connected",
    "mem_usage": "512 MB",
    "cpu_temp": "48°C",
    "cpu_percent": 12.5,
    "gpio_used_count": 3,
    "spi_buses": 1,
    "i2c_buses": 1,
    "usb_devices_count": 2,
    "net_bytes_sent": 102400,
    "net_bytes_recv": 204800,
    "net_ifaces": ["wlan0", "eth0"]
}

with SessionLocal() as db:
    dev = db.query(DeviceStatus).filter_by(raspberry_id=payload["raspberry_id"]).first()
    if not dev:
        dev = DeviceStatus(raspberry_id=payload["raspberry_id"])
        db.add(dev)

    dev.wifi_status = payload["wifi_status"]
    dev.mem_usage = payload["mem_usage"]
    dev.cpu_temp = payload["cpu_temp"]
    dev.cpu_percent = payload["cpu_percent"]
    dev.gpio_used_count = payload["gpio_used_count"]
    dev.spi_buses = payload["spi_buses"]
    dev.i2c_buses = payload["i2c_buses"]
    dev.usb_devices_count = payload["usb_devices_count"]
    dev.net_bytes_sent = payload["net_bytes_sent"]
    dev.net_bytes_recv = payload["net_bytes_recv"]
    dev.net_ifaces = json.dumps(payload["net_ifaces"])
    dev.last_update = datetime.utcnow()

    db.commit()
```

- Registrar ação de LED:
```python
from database import SessionLocal, LEDHistory
from datetime import datetime

with SessionLocal() as db:
    entry = LEDHistory(
        raspberry_id="raspberry-01",
        led_type="external",
        pin=17,
        action="on",
        timestamp=datetime.utcnow()
    )
    db.add(entry)
    db.commit()
```

- Cadastrar/atualizar uma tag RFID (uid único):
```python
from database import SessionLocal, RFIDTag

with SessionLocal() as db:
    uid = "04:A1:B2:C3"
    tag = db.query(RFIDTag).filter_by(uid=uid).first()
    if not tag:
        tag = RFIDTag(uid=uid, name="Cartão João", raspberry_id="raspberry-01")
        db.add(tag)
    else:
        tag.name = "Cartão João (atualizado)"
    db.commit()
```

- Registrar leitura RFID e atualizar status do dispositivo:
```python
from datetime import datetime
from database import SessionLocal, RFIDReadHistory, DeviceStatus

with SessionLocal() as db:
    uid = "04:A1:B2:C3"
    tag_name = "Cartão João"
    rasp_id = "raspberry-01"

    db.add(RFIDReadHistory(uid=uid, tag_name=tag_name, raspberry_id=rasp_id))
    dev = db.query(DeviceStatus).filter_by(raspberry_id=rasp_id).first()
    if dev:
        dev.last_rfid_read = datetime.utcnow()
        dev.rfid_reader_status = "online"
    db.commit()
```

## Configuração do banco por ambiente

Por padrão:
```python
DATABASE_URL = "sqlite:///./raspberry_data.db"
```

Para tornar configurável por ambiente:
```python
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./raspberry_data.db")
```

Exemplos de URLs:
- SQLite: `sqlite:///./raspberry_data.db`
- PostgreSQL: `postgresql+psycopg2://user:pass@host:5432/dbname`
- MySQL: `mysql+pymysql://user:pass@host:3306/dbname`

Observações:
- O parâmetro `connect_args={"check_same_thread": False}` é específico do SQLite para permitir uso em múltiplas threads. Retire-o ao usar bancos client/server.
- Em produção, prefira PostgreSQL para concorrência e tipos nativos (ex.: JSONB).

## Boas práticas

- Sessões: crie uma por requisição/tarefa e feche sempre (use context manager).
- Mutações frequentes: mantenha `commit()` curto e trate exceções com `rollback()`.
- Campos JSON: para `net_ifaces`, considere migrar para tipo JSON nativo (PostgreSQL) no futuro.
- Índices: já existem em `raspberry_id`, `uid` e `timestamp` de leituras para acelerar consultas comuns.
- Migrações: use Alembic para evoluir o schema:
  - `alembic init migrations`
  - configure `sqlalchemy.url` no `alembic.ini`
  - `alembic revision --autogenerate -m "mensagem"`
  - `alembic upgrade head`

## Solução de problemas

- Arquivo SQLite bloqueado:
  - Evite acessos concorrentes pesados. Para alta concorrência, use PostgreSQL.
- Colunas ausentes após alterar modelos:
  - Rode migrações (Alembic) ou recrie o banco (apenas em dev).
- Erros de thread no SQLite:
  - Garanta que `check_same_thread=False` esteja configurado (já está no código).

## Compatibilidade (SQLAlchemy)

- O código usa `declarative_base()` de `sqlalchemy.ext.declarative`. Em SQLAlchemy 2.x, você pode migrar para:
  ```python
  from sqlalchemy.orm import declarative_base
  Base = declarative_base()
  ```
  ou o novo estilo:
  ```python
  from sqlalchemy.orm import DeclarativeBase
  class Base(DeclarativeBase):
      pass
  ```
- A API atual funciona bem tanto na 1.4 quanto na 2.x (modo compatibilidade).
# Consumer de Health Check para Raspberry Pi (RabbitMQ → Banco)

Este serviço consome mensagens de health check enviadas por Raspberries via RabbitMQ e persiste/atualiza o status de cada dispositivo em um banco de dados usando SQLAlchemy.

Ele pode rodar tanto em foreground quanto em uma thread dedicada, permitindo integração simples com aplicações web ou workers.

## Objetivo

- Centralizar métricas e informações de saúde de múltiplas Raspberries.
- Atualizar (ou criar) o registro do dispositivo com base no `raspberry_id` recebido.
- Manter histórico do último update e campos técnicos úteis (CPU, memória, rede, GPIO, etc.).
- Facilitar o consumo via RabbitMQ de forma resiliente e desacoplada do produtor.

## Como funciona (visão rápida)

- Conecta no RabbitMQ usando as credenciais `athavus`/`1234`, host `localhost`, vhost `/`.
- Declara a fila durável `rasp_data`.
- Consome mensagens JSON. Para cada mensagem:
  - Adiciona o payload em memória em `shared.received_messages` (útil para debug/telemetria).
  - Faz “upsert” no banco:
    - Se existir `DeviceStatus` com o `raspberry_id`, atualiza campos.
    - Se não existir, cria um novo registro.
  - Converte `net_ifaces` para string JSON antes de salvar.
  - Define `last_update` (UTC) em updates de registros existentes.

## Estrutura do projeto (mínima esperada)

- `database.py`: expõe `SessionLocal` (sessionmaker do SQLAlchemy) e o modelo `DeviceStatus`.
- `shared.py`: expõe uma lista `received_messages = []`.
- O arquivo com o código do consumer (este).

Exemplo (simplificado) do modelo esperado:
```python
# database.py (exemplo simplificado)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///db.sqlite3")  # ajuste para seu banco
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class DeviceStatus(Base):
    __tablename__ = "device_status"

    id = Column(Integer, primary_key=True, index=True)
    raspberry_id = Column(String, unique=True, index=True, nullable=False)
    wifi_status = Column(String)
    mem_usage = Column(String)
    cpu_temp = Column(String)
    led_internal_status = Column(Boolean, default=False)
    led_external_status = Column(Boolean, default=False)
    # Campos opcionais suportados pelo código:
    cpu_percent = Column(Float, nullable=True)
    gpio_used_count = Column(Integer, nullable=True)
    spi_buses = Column(Text, nullable=True)      # pode armazenar JSON string
    i2c_buses = Column(Text, nullable=True)      # pode armazenar JSON string
    usb_devices_count = Column(Integer, nullable=True)
    net_bytes_sent = Column(Integer, nullable=True)
    net_bytes_recv = Column(Integer, nullable=True)
    net_ifaces = Column(Text, nullable=True)     # armazena JSON string
    last_update = Column(DateTime, default=datetime.utcnow)
```

## Pré-requisitos

- Python 3.9+
- RabbitMQ acessível
- Um banco de dados suportado pelo SQLAlchemy (SQLite, PostgreSQL, etc.)
- Dependências Python:
  - `pika`
  - `SQLAlchemy`
  - (Opcional) driver do banco (ex.: `psycopg2-binary` para PostgreSQL)

Instalação das dependências:
```bash
pip install pika SQLAlchemy
# E o driver do seu banco, por exemplo:
# pip install psycopg2-binary
```

## Configurando o RabbitMQ

Você pode subir um RabbitMQ local via Docker com as credenciais esperadas:

```yaml
# docker-compose.yml
version: "3.9"
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: athavus
      RABBITMQ_DEFAULT_PASS: 1234
      RABBITMQ_DEFAULT_VHOST: /
```

```bash
docker compose up -d
# Painel de gestão: http://localhost:15672 (login: athavus / 1234)
```

Importante: em produção, use credenciais seguras e variáveis de ambiente.

## Execução

Você pode iniciar o consumer diretamente ou em uma thread:

- Direto (bloqueante):
```python
from seu_modulo import rabbit_consumer

rabbit_consumer()
```

- Em thread (não bloqueante):
```python
from seu_modulo import start_consumer_thread, shared

start_consumer_thread()
# siga com sua aplicação (ex.: FastAPI/Flask) enquanto o consumer roda ao fundo
```

A lista `shared.received_messages` manterá os payloads recebidos (útil para depurar ou expor via endpoint). Se for usá-la amplamente em produção, considere trocar por uma estrutura thread-safe ou cache externo.

## Publicando uma mensagem de teste

Formato JSON esperado (exemplo):
```json
{
  "id": "raspberry-01",
  "wifi_status": "connected",
  "mem_usage": "512 MB",
  "cpu_temp": "48°C",
  "cpu_percent": 12.5,
  "gpio_used_count": 3,
  "spi_buses": ["spi0.0"],
  "i2c_buses": ["i2c-1"],
  "usb_devices_count": 2,
  "net_bytes_sent": 102400,
  "net_bytes_recv": 204800,
  "net_ifaces": [
    {"name": "wlan0", "ip": "192.168.0.10"}
  ]
}
```

Snippet para publicar:
```python
import pika, json

credentials = pika.PlainCredentials('athavus', '1234')
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost', 5672, '/', credentials)
)
channel = connection.channel()
channel.queue_declare(queue='rasp_data', durable=True)

msg = {
  "id": "raspberry-01",
  "wifi_status": "connected",
  "mem_usage": "512 MB",
  "cpu_temp": "48°C",
  "cpu_percent": 12.5,
  "gpio_used_count": 3,
  "spi_buses": ["spi0.0"],
  "i2c_buses": ["i2c-1"],
  "usb_devices_count": 2,
  "net_bytes_sent": 102400,
  "net_bytes_recv": 204800,
  "net_ifaces": [{"name":"wlan0","ip":"192.168.0.10"}]
}

channel.basic_publish(
    exchange='',
    routing_key='rasp_data',
    body=json.dumps(msg),
    properties=pika.BasicProperties(delivery_mode=2)  # persistente
)
print("Mensagem publicada.")
connection.close()
```

## Mapeamento de campos

- id → DeviceStatus.raspberry_id
- wifi_status → texto (ex.: connected, disconnected, unknown)
- mem_usage → texto (ex.: “512 MB”)
- cpu_temp → texto (ex.: “48°C”)
- cpu_percent → float (opcional)
- gpio_used_count → inteiro (opcional)
- spi_buses, i2c_buses → salvos como string JSON (coluna Text recomendada)
- usb_devices_count → inteiro (opcional)
- net_bytes_sent, net_bytes_recv → inteiros (opcionais)
- net_ifaces → salvo como string JSON
- last_update → datetime UTC (atualizado em updates; para novos registros, use default no modelo)

Observações:
- Campos “extras” são preenchidos com `setattr`. Se seu modelo não tiver essas colunas, adapte o modelo (ou remova do código).
- `auto_ack=True` está habilitado — mensagens são confirmadas assim que entregues ao callback. Para cenários críticos, avalie usar `auto_ack=False` + `basic_ack` após `commit()`.

## Boas práticas e considerações

- Configuração: troque credenciais hardcoded por variáveis de ambiente.
- Confiabilidade: considere `basic_qos(prefetch_count=...)` e `auto_ack=False` para evitar perda em caso de falha durante o processamento.
- Observabilidade: adicione logs estruturados e métricas (ex.: Prometheus).
- Esquema: se possível, use tipo JSON nativo no banco (PostgreSQL) para `net_ifaces`, `spi_buses`, `i2c_buses`.
- Índices: crie índice em `raspberry_id` e, se necessário, em `last_update`.
- Reconexão: o código atual não implementa reconexão automática ao RabbitMQ. Em produção, adicione retry/backoff.

## Solução de problemas

- Erro ao conectar no RabbitMQ:
  - Verifique host/porta/credenciais e se a fila `rasp_data` existe.
  - Se usar Docker, confirme as portas e o vhost.
- Erro no banco ou colunas inexistentes:
  - Garanta que o modelo `DeviceStatus` contém as colunas usadas.
  - Rode migrações ou ajuste o modelo conforme os campos opcionais.
- Erro ao decodificar JSON:
  - Confira se o produtor está enviando JSON válido com o campo `id`.
- Mensagens “somem”:
  - Com `auto_ack=True`, se o processo cair durante o callback, a mensagem já estará acked. Avalie trocar para ack manual.

<div align="center">
  <img src="./docs/assets/virtus.png">
</div>

# Mini‑cluster de Controle de Acesso por RFID com Raspberries

Mensageria com RabbitMQ + Python (pika/psutil) + SQLAlchemy/SQLite + Frontend (VueJs)

Este projeto implementa a base de um mini‑cluster para controle de acesso a portas utilizando múltiplas Raspberry Pis. Cada Raspberry coleta métricas (health check) e, futuramente, eventos de leitura RFID, enviando-os ao broker RabbitMQ. Um serviço central (consumer) processa as mensagens, atualiza o estado dos dispositivos e persiste dados no banco. Um frontend (a ser adicionado) exibirá dashboards e permitirá gestão de tags e eventos.

- Multi‑Raspberry (nós da borda) conectadas a um nó central
- Transporte assíncrono via RabbitMQ
- Persistência com SQLAlchemy/SQLite (pronto para evoluir para PostgreSQL)
- Modelos para LED, RFID e status de dispositivos
- Frontend em VueJS

## Visão geral da arquitetura

- Nós de borda (Raspberries): publicam health checks e, futuramente, leituras RFID.
- Broker (RabbitMQ): intermedia mensagens de forma confiável.
- Nó central (Consumer): faz upsert de DeviceStatus, guarda históricos e integra regras de acesso.
- Banco: armazena status, tags RFID e histórico de leituras.
- Frontend: visualização e administração (pendente de integração).

Fluxo (atual + previsto):
- Health check: Raspberry → fila rasp_data → Consumer → DeviceStatus
- RFID (planejado): Raspberry (leitor) → fila rfid_reads → Serviço de autorização → (opcional) comando para atuador/LED → histórico e status

Diagrama (alto nível):
Raspberries (publisher) → RabbitMQ → Consumer (Python) → Banco de Dados → Frontend

## Componentes

- publisher.py (nós Raspberry)
  - Coleta métricas com psutil e publica 1 msg/segundo na fila rasp_data
  - Identificação automática via hostname
- consumer.py (nó central)
  - Consome a fila rasp_data, atualiza/cria DeviceStatus e mantém last_update
  - Pode rodar em thread de fundo (útil com APIs)
  - Armazena net_ifaces como JSON string
- database.py
  - Modelos: DeviceStatus, LEDHistory, RFIDTag, RFIDReadHistory
  - Engine + SessionLocal + init_db() + get_db()
  - Banco padrão: sqlite:///./raspberry_data.db
- shared.py
  - Lista received_messages (buffer simples em memória para debug)

## Banco de dados (modelos)

- DeviceStatus: estado atual por Raspberry (CPU, memória, rede, RFID/LEDs, timestamps)
- LEDHistory: trilha ações de LED (ex.: on/off/blink)
- RFIDTag: cadastro de UIDs e nomes amigáveis
- RFIDReadHistory: histórico de leituras (UID, nome, Raspberry, timestamp)

Observação: net_ifaces é gravado como string JSON; use json.dumps/json.loads.

## Requisitos

- Python 3.9+
- RabbitMQ acessível
- Dependências:
  - pika (mensageria)
  - psutil (publisher/saúde)
  - SQLAlchemy
  - (opcional) driver do banco: psycopg2-binary (PostgreSQL), PyMySQL (MySQL)

## Configuração do RabbitMQ

Docker Compose (dev):
```yaml
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

- Console: http://localhost:15672 (athavus/1234)
- Em produção, use credenciais/ACLs seguras e, se possível, TLS.

## Como executar (desenvolvimento)

1) Suba o RabbitMQ (Docker) e confirme acesso ao painel
2) Crie e ative um ambiente virtual
   - Linux/Mac: `python -m venv .venv && source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
3) Instale dependências
   - `pip install pika psutil SQLAlchemy`
4) Inicie o Consumer (nó central)
   - `python consumer.py`
   - Log esperado: “RabbitMQ consumer iniciado”
5) Inicie o Publisher (em cada Raspberry)
   - Ajuste o host do RabbitMQ no script (IP do servidor)
   - `python publisher.py`
   - Pare com CTRL+C
6) Consulte dados
   - `sqlite3 raspberry_data.db "select raspberry_id,wifi_status,cpu_temp,last_update from device_status;"`

Dica: o consumer atual usa `auto_ack=True`. Para produção, considere ack manual após commit.

## Formato das mensagens (health check)

Exemplo publicado na fila rasp_data:
```json
{
  "id": "raspberrypi",
  "mem_usage": "512 MB",
  "cpu_temp": "48.1°C",
  "wifi_status": "online",
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

O consumer mapeia:
- id → DeviceStatus.raspberry_id
- net_ifaces → JSON serializado (string)
- last_update → atualizado em cada mensagem

## Controlo de acesso (RFID) — escopo e próximos passos

Os modelos já contemplam RFID (RFIDTag e RFIDReadHistory) e status do leitor (DeviceStatus.rfid_reader_status). A integração de leitura/decisão de acesso segue este desenho:

- Leitura RFID (Raspberry/porta)
  - Serviço de leitor publica UID + raspberry_id + timestamp em uma fila (ex.: rfid_reads)
- Autorização (nó central)
  - Consulta RFIDTag (autorizado/não autorizado), grava RFIDReadHistory
  - Opcional: registra LEDHistory e envia comando de “liberar/negado” para o nó da porta (ex.: fila door_commands)
- Execução local
  - Raspberry aciona o atuador (relé/fechadura) e LEDs correspondentes

Itens a implementar/integração:
- Serviço de leitura RFID no nó da porta (publisher de rfid_reads)
- Serviço de autorização/comandos no nó central
- Topologias/filas adicionais (rfid_reads, door_commands)
- Frontend: cadastro de tags, auditoria e dashboards

Se quiser, posso fornecer os esboços desses serviços e as mensagens padrão.

## Boas práticas (produção)

- Mensageria:
  - `auto_ack=False` + `basic_ack` após `commit()` para garantir entrega
  - `basic_qos(prefetch_count=N)` para controlar concorrência
  - Reconexão com backoff exponencial no publisher e consumer
- Segurança:
  - Usuários/ACLs dedicados no RabbitMQ, rotação de senhas, TLS
  - Mínimos privilégios para Raspberries (publicar somente nas filas necessárias)
- Banco:
  - Considere PostgreSQL (JSONB, concorrência, backups/replicação)
  - Migrações com Alembic
- Observabilidade:
  - Logging estruturado, métricas (Prometheus), dashboards
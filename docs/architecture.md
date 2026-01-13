# Arquitetura do Sistema

Este documento descreve o fluxo de dados e os componentes do **Raspberry Gate**.

## Visão Geral

O sistema opera em um modelo **Híbrido (Push/Pull)**:
1.  **Push (Telemetry)**: Os nós Raspberry enviam dados via **RabbitMQ** para o servidor.
2.  **Pull/RPC (API)**: O Frontend consulta o servidor via **HTTP/REST** e envia comandos.

## Diagramas de Sequência

### 1. Fluxo de Health Check (Monitoramento)

```mermaid
sequenceDiagram
    participant Pi as Raspberry Pi Node
    participant MQ as RabbitMQ (Queue: rasp_data)
    participant Consumer as Server Consumer
    participant DB as Database (SQLite)
    participant Client as Frontend (Vue)

    loop Every 1s
        Pi->>Pi: Coleta CPU/RAM/Temp
        Pi->>MQ: Publica JSON {metrics}
    end

    MQ->>Consumer: Entrega Mensagem
    Consumer->>DB: Upsert DeviceStatus
    
    loop Every 5s
        Client->>Client: Poll API /api/devices/status
        Client->>DB: Select * from DeviceStatus
        DB-->>Client: Lista de dispositivos atualizada
    end
```

### 2. Fluxo de Acesso (RFID)

```mermaid
sequenceDiagram
    participant User as Usuário
    participant Reader as Leitor RFID (Raspberry)
    participant Serv as Server API
    participant DB as Database
    participant Lock as Servo Motor

    User->>Reader: Aproxima Cartão (UID)
    Reader->>Reader: Lê UID
    Reader->>Serv: POST /api/rfid/read {uid, rasp_id}
    
    Serv->>DB: Consulta RFIDTag (Nome)
    DB-->>Serv: Nome da Tag (se existir)
    
    Serv->>DB: Insert RFIDReadHistory
    
    alt Tag Detectada (Regra Simples)
        Serv->>Lock: Comando Open (GPIO/Servo)
        Lock-->>Serv: Sucesso
        Serv->>DB: Insert DoorOpenHistory
    end
    
    Serv-->>Reader: 200 OK
```

## Stack Tecnológica

| Camada | Tecnologia | Motivação |
|--------|------------|-----------|
| **Edge** | Python, RPi.GPIO | Acesso fácil ao hardware, rico ecossistema. |
| **Broker** | RabbitMQ | Desacoplamento, buffers para evitar perda de dados se o server cair. |
| **Backend** | FastAPI, SQLAlchemy | Alta performance, assíncrono, validação automática (Pydantic). |
| **DB** | SQLite (Dev) / Postgres | Leve para dev, robusto para prod. |
| **Frontend** | Vue 3, Tailwind | Reatividade moderna, desenvolvimento rápido. |

## Decisões de Design

1.  **API Gateway Unificado**: O `server/main.py` roda tanto a API REST para o cliente quanto a thread do Consumer do RabbitMQ. Isso simplifica o deployment em ambientes pequenos (não precisa de 2 containers separados).
2.  **Identificação por Hostname**: As Raspberries se auto-identificam pelo hostname. Isso facilita a escalabilidade (basta plugar uma nova rasp na rede).
3.  **Histórico Temporal**: Além do status atual, guardamos histórico (`DeviceStatusHistory`) para plotar gráficos de temperatura/uso no futuro.

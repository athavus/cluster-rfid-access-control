# Raspberry Pi 5 IoT API

API de gerenciamento de clusters Raspberry Pi, com controle de LEDs via GPIO, leitura, cadastro e histórico de RFID, monitoramento de dispositivos, integração RabbitMQ, health check e endpoints para dados em tempo real.

## Visão Geral

Esta API fornece recursos essenciais para ambiente IoT embarcado em Raspberry Pi, permitindo o controle remoto de LEDs (interno e externo), leitura e gerenciamento de tags RFID, armazenamento de histórico e status do equipamento, além de integração nativa com fila RabbitMQ para monitoramento em tempo real.

***

## Funcionalidades

- Controle remoto de LEDs internos e externos via GPIO.
- Registro, atualização, listagem e remoção de tags RFID.
- Histórico detalhado de operações em LEDs e leituras RFID.
- Monitoramento de status dos dispositivos cadastrados.
- API aberta para recebimento e exibição de dados em tempo real.
- Endpoints de health check e estatísticas do sistema.

***

## Instalação

### Pré-requisitos

- Python 3.9+ instalado.
- Raspberry Pi 5 (ou compatível) com GPIO configurado.
- Banco de dados SQLite ou compatível com SQLAlchemy.
- RabbitMQ disponível na rede.

***

## Como Usar

- Os endpoints REST estão disponíveis após iniciar o servidor.
- Doc automática: acesse `/docs` na URL base do seu servidor para explorar e testar os endpoints visualmente.
- Use ferramentas como Postman, Insomnia ou cURL para testar manualmente.

***

## Documentação dos Endpoints

Endpoints principais por categoria:

| Caminho                       | Verbo | Descrição                              |
|-------------------------------|-------|----------------------------------------|
| `/api/led/control`            | POST  | Controla LED: liga/desliga via GPIO.   |
| `/api/led/{led_type}/on`      | POST  | Liga LED interno ou externo.           |
| `/api/led/{led_type}/off`     | POST  | Desliga LED interno ou externo.        |
| `/api/led/status`             | GET   | Consulta status dos LEDs.              |
| `/api/led/history`            | GET   | Lista histórico de comandos LED.       |
| `/api/rfid/read`              | POST  | Recebe evento de leitura RFID.         |
| `/api/rfid/tag`               | POST  | Cria/atualiza nome de tag RFID.        |
| `/api/rfid/tags`              | GET   | Lista todas as tags RFID.              |
| `/api/rfid/tag/{uid}`         | GET   | Busca dados de tag específica.         |
| `/api/rfid/tag/{uid}`         | DELETE| Remove uma tag RFID.                   |
| `/api/rfid/history`           | GET   | Histórico de leituras RFID.            |
| `/api/rfid/stats`             | GET   | Estatísticas de leituras RFID.         |
| `/api/devices/status`         | GET   | Status de todos os dispositivos.       |
| `/api/devices/{id}/status`    | GET   | Status de um dispositivo.              |
| `/api/data/realtime`          | GET   | Lista dados recebidos em tempo real.   |
| `/api/data`                   | POST  | Envia dados em tempo real.             |
| `/health`, `/`                | GET   | Health check da API.                   |
| `/api/stats`                  | GET   | Estatísticas gerais do sistema.        |

***

## Estrutura do Projeto

- **main.py:** Arquivo principal da aplicação FastAPI.
- **consumer.py:** Integração RabbitMQ (consumo de mensagens).
- **gpio_handler.py:** Lógica de controle GPIO para LEDs.
- **rfid_handler.py:** Lógica de leitura e polling de RFID.
- **database.py:** Modelos e rotinas do banco de dados com SQLAlchemy.
- **schemas.py:** Schemas Pydantic para validação.
- **shared.py:** Utilidades compartilhadas entre módulos.
# Publicador de Health Check para Raspberry Pi (RabbitMQ → fila rasps_data)

Este script roda na Raspberry Pi (ou em qualquer Linux compatível) e publica, a cada segundo, métricas de saúde do sistema em uma fila RabbitMQ. Ele é o par “produtor” do consumer que grava esses dados no banco.

Perfeito para monitorar múltiplos dispositivos, com identificação dinâmica por hostname e payloads persistentes na fila.

## Objetivo

- Coletar métricas locais (CPU, memória, temperatura, rede, buses) de forma leve.
- Enviar mensagens JSON para a fila `rasp_data` no RabbitMQ.
- Identificar cada dispositivo automaticamente pelo hostname.
- Produzir dados com timestamp para auditoria/telemetria.

## Como funciona

- Coleta de métricas com `psutil` e leitura direta do sistema:
  - Memória usada, CPU% (instantâneo), temperatura da CPU (`/sys/class/thermal/thermal_zone0/temp`, quando disponível).
  - Status do Wi‑Fi com base na existência de `wlan0`.
  - Quantidade de buses SPI e I2C via dispositivos em `/dev`.
  - Contagem de dispositivos USB via sysfs.
  - Tráfego de rede total (bytes enviados/recebidos).
  - Interfaces de rede ativas (nomes).
- Conecta no RabbitMQ com credenciais definidas no código.
- Declara a fila durável `rasp_data`.
- Publica 1 mensagem/segundo com:
  - id: hostname da máquina.
  - métricas coletadas.
  - timestamp (epoch em segundos).
- Mensagens são marcadas como persistentes (`delivery_mode=2`).
- Encerra com CTRL+C.

## Pré-requisitos

- Python 3.9+
- Dependências:
  - `psutil`
  - `pika`
- Acesso ao RabbitMQ (host/porta/credenciais).
- Para métricas específicas:
  - Temperatura da CPU: disponível por padrão no Raspberry Pi OS. Em outros ambientes pode retornar “N/A”.
  - SPI/I2C: se quiser contar corretamente, habilite em raspi-config (embora a contagem de nós em `/dev` já funcione como “detector”).

Instalação:
```bash
pip install psutil pika
```

## Configuração

No código, ajuste conforme seu ambiente:
- Host RabbitMQ: atualmente `"192.168.130.9"`.
- Porta/vhost/credenciais: `5672`, `/`, `athavus` / `1234`.
- Nome da fila: `rasp_data`.

Dicas:
- Em produção, substitua credenciais hardcoded por variáveis de ambiente.
- Se sua interface Wi‑Fi não for `wlan0` (ex.: `wlp3s0`), adapte a detecção no trecho do `wifi_status`.

## Execução

Execute diretamente no dispositivo:
```bash
python3 publisher.py
```

Saída esperada (exemplo):
```
Iniciando publicação ampliada de health check para Raspberry raspberrypi
Pressione CTRL+C para parar

[14:22:03] Rasp raspberrypi: {...payload JSON...}
[14:22:04] Rasp raspberrypi: {...payload JSON...}
...
```

Interrompa com CTRL+C. Ao sair, o script fecha a conexão com o RabbitMQ e reporta o total de mensagens enviadas.

## Formato da mensagem

Exemplo de payload publicado:
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

Observações de compatibilidade:
- `spi_buses` e `i2c_buses` aqui são contagens (inteiros). Se seu consumer espera listas, adapte de acordo (ex.: listar os dispositivos ao invés de contar).
- `net_ifaces` é uma lista de nomes de interfaces ativas; se quiser IPs/detalhes, estenda usando `psutil.net_if_addrs()`.

## Campos coletados

- id: hostname do dispositivo (via `socket.gethostname()`).
- mem_usage: memória usada em MB (string).
- cpu_temp: temperatura da CPU (string, “N/A” se indisponível).
- wifi_status: “online” se `wlan0` existir; “unknown” caso contrário.
- cpu_percent: uso de CPU em % no instante (primeira leitura pode retornar 0).
- gpio_used_count: 0 por padrão (placeholder para futura implementação).
- spi_buses: quantidade de dispositivos `/dev/spidev*`.
- i2c_buses: quantidade de dispositivos `/dev/i2c-*`.
- usb_devices_count: contagem de entradas em `/sys/bus/usb/devices/*usb*`.
- net_bytes_sent/net_bytes_recv: bytes totais (desde boot) pelo sistema.
- net_ifaces: lista de interfaces com `isup=True`.
- timestamp: epoch em segundos (float).

## Boas práticas

- Frequência de publicação: ajustável alterando `time.sleep(1)` (ex.: 5 segundos para reduzir tráfego).
- Robustez: hoje, se a conexão ao RabbitMQ falhar na criação, o script encerra; dentro do loop, erros são tratados com retry simples (sleep de 1s). Para produção, considere reconexão com backoff exponencial.
- Logs: use logging estruturado ao invés de prints se integrar com observabilidade.
- Segurança: evite credenciais em código. Use variáveis de ambiente e usuários com permissões mínimas no RabbitMQ.

## Solução de problemas

- Erro ao conectar no RabbitMQ:
  - Verifique IP/porta/credenciais e firewall.
  - Confirme se a fila `rasp_data` existe (o script declara se não existir).
- Temperatura “N/A”:
  - Em hardware não-Raspberry ou distros sem o caminho `thermal_zone0`, é esperado.
- Wi‑Fi “unknown”:
  - Interface pode não ser `wlan0`. Ajuste o código para o nome correto ou detecte dinamicamente.
- `spi_buses`/`i2c_buses` retornam 0:
  - Habilite SPI/I2C no sistema e confirme a presença de `/dev/spidev*` e `/dev/i2c-*`.

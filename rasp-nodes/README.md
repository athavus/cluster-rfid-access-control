# Rasp-Nodes (Edge Code)

Este diretório contém o código que deve ser executado nas placas **Raspberry Pi** (os "nós" do cluster). Ele é responsável por interagir com o hardware local e comunicar com o servidor central.

## Funcionalidades

*   **Monitoramento (Health Check)**: Coleta e envia dados de CPU, RAM, Disco, Rede e Temperatura a cada segundo.
*   **Interface Local**:
    *   Display OLED (SSD1306): Mostra IP, Status e Mensagens.
    *   Botões Físicos: Navegação em menus locais (ex.: Seleção de WiFi).
*   **Controle de Acesso**:
    *   Leitor RFID (MFRC522): Leitura de tags e envio para validação.
    *   Atuadores: Controle de Servo/Relé para abrir portas.

## Hardware Suportado

*   Raspberry Pi 3/4/Zero W
*   Display OLED I2C 128x64 (Driver SSD1306)
*   Leitor RFID RC522 (SPI)
*   Botões (GPIO)
*   Servo Motor (PWM/GPIO)

## Instalação na Raspberry Pi

### 1. Preparar Sistema
Instale as dependências do sistema operacional:
```bash
sudo apt update
sudo apt install python3-venv python3-dev swig liblgpio-dev i2c-tools
```
*Habilite as interfaces I2C e SPI via `sudo raspi-config`.*

### 2. Configurar Ambiente Python
```bash
# Na pasta rasp-nodes/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuração
Verifique os arquivos de configuração em `controllers/` e `system/`:
*   **Teclado/Input**: Se usar botões emulados ou dispositivos específicos, ajuste em `controllers/keyboard.py`.
*   **RabbitMQ**: Configure o host do RabbitMQ se não estiver rodando localmente (edite `publisher.py` ou use variáveis de ambiente se suportado).

### 4. Executar
```bash
sudo env PATH=$PATH python main.py
```
*(O uso de `sudo` pode ser necessário para acesso direto ao hardware GPIO/SPI em algumas distros).*

## Estrutura

*   `main.py`: Ponto de entrada. Inicializa o loop principal.
*   `system/`: Lógica de estados da aplicação (modos Conectado, Desconectado, Seleção de WiFi).
*   `controllers/`: Drivers de hardware (Display, Botões, WiFi, GPIO).

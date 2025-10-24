# Guia de Instalação e Execução do Projeto

Este guia descreve como configurar, instalar e executar corretamente o projeto em seu ambiente local.

---

## 1. Criar e Ativar o Ambiente Virtual

É **necessário criar e ativar uma virtual environment (venv)** antes de utilizar o projeto.

```bash
python -m venv venv
```

### Ativar o ambiente virtual

- **Bash:**
  ```bash
  source venv/bin/activate
  ```

- **Fish:**
  ```bash
  source venv/bin/activate.fish
  ```

---

## 2. Instalar Dependências do Sistema

Após ativar o ambiente virtual, instale as dependências necessárias.

### Dependências do sistema operacional

```bash
sudo apt install swig liblgpio-dev
```

### Dependências do Python

```bash
pip install -r requirements.txt
```

Após isso, todas as dependências estarão instaladas corretamente.

---

## 3. Configuração do Teclado

Para configurar o teclado utilizado pelo sistema:

1. Liste os dispositivos de entrada disponíveis:
   ```bash
   ls /dev/input/
   ```

2. Identifique o **event** correspondente ao seu teclado.

3. No arquivo `controllers/keyboard.py`, **na linha 4**, substitua o caminho atual pelo **event** identificado.

---

## 4. Executar o Sistema

Após realizar a configuração, execute o sistema com o comando:

```bash
python main.py
```

---

## 5. Possíveis Conflitos de Dependências

Em alguns sistemas podem ocorrer conflitos entre versões de bibliotecas.
É importante consultar a documentação das principais dependências utilizadas.

### Adafruit Circuit Python SSD1306

[https://github.com/adafruit/Adafruit_CircuitPython_SSD1306](https://github.com/adafruit/Adafruit_CircuitPython_SSD1306)

---

### Erro Comum: `NameError: name 'DigitalInOut' is not defined`

Esse erro pode ocorrer no arquivo:

```
venv/lib/python3.13/site-packages/adafruit_bus_device/spi_device.py
```

#### Trecho original problemático

```python
import time

try:
    from types import TracebackType
    from typing import Optional, Type

    # Used only for type annotations.
    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass
```

#### Solução

Reorganize os imports da seguinte forma:

```python
import time
from digitalio import DigitalInOut

try:
    from types import TracebackType
    from typing import Optional, Type

    # Used only for type annotations.
    from busio import SPI
except ImportError:
    pass
```

Após essa correção, o erro deve desaparecer.  
Se não houver novas mensagens de erro, o projeto está pronto para execução.

---

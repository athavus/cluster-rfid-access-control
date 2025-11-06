# Assets - Logo e Recursos

## Logo da Apresentação

Este diretório contém os arquivos relacionados à logo do projeto.

### Arquivo: `logo_bitmap.py`

Este arquivo contém o bitmap da logo no formato compatível com o display OLED SSD1306 (128x64 pixels, monocromático).

### Como adicionar sua logo:

#### Opção 1: Usando o script de conversão (recomendado)

Se você tem a logo em formato de imagem (PNG, JPG, etc):

```bash
python assets/convert_logo.py caminho/para/sua/logo.png
```

O script irá:
- Redimensionar a imagem para 128x64 pixels
- Converter para monocromático (preto e branco)
- Gerar o arquivo `logo_bitmap.py` com o byte array correto

#### Opção 2: Adicionar byte array manualmente

Se você já tem o byte array da logo:

1. Edite o arquivo `logo_bitmap.py`
2. Substitua a linha:
   ```python
   logo_bitmap_bytes = bytearray(1024)
   ```
   
   Por:
   ```python
   logo_bitmap_bytes = bytearray([...])  # seu byte array aqui
   ```

### Formato do Byte Array

- Tamanho: 1024 bytes (128x64 pixels / 8 bits por byte)
- Formato: SSD1306 vertical packing
  - Cada byte representa 8 pixels verticais consecutivos
  - Para cada coluna x (0-127), temos 8 bytes (uma página)
  - Byte índice = x + (y_page * 128), onde y_page = 0-7
  - Dentro de cada byte, o bit menos significativo (LSB) representa o pixel superior

### Script de Conversão

O arquivo `convert_logo.py` pode ser usado para converter qualquer imagem para o formato necessário.

**Requisitos:**
- Python 3
- Pillow (PIL): `pip install pillow`

**Uso:**
```bash
python assets/convert_logo.py logo.png
```


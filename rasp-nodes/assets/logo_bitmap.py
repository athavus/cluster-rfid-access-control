"""
Arquivo para armazenar o bitmap da logo.
Substitua o array logo_bitmap_bytes pelo seu byte array da logo.

O bitmap deve ser uma imagem monocromática de 128x64 pixels (ou menor, será centralizada).
Formato: bytes representando pixels em modo "1" (1 bit por pixel, 0=preto, 1=branco)
"""

# Array de bytes da logo (128x64 = 8192 bits = 1024 bytes)
# Substitua este array pelo seu byte array real
# Exemplo de estrutura vazia (tela preta):
logo_bitmap_bytes = bytearray(1024)  # 128x64 / 8 = 1024 bytes

# Alternativa: se você tiver uma imagem PNG/JPG, pode usar:
# from PIL import Image
# logo_image = Image.open("logo.png").convert("1").resize((128, 64))

# Se você já tem o byte array, substitua a linha acima por:
# logo_bitmap_bytes = b'...'  # seu byte array aqui


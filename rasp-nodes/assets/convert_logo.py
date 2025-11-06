#!/usr/bin/env python3
"""
Script auxiliar para converter uma imagem (PNG, JPG, etc) para o formato
de byte array compatível com o display OLED SSD1306 (128x64, monocromático).

Uso:
    python convert_logo.py logo.png

O script irá gerar/atualizar o arquivo logo_bitmap.py com o byte array da imagem.
"""

import sys
from PIL import Image

def image_to_bitmap_bytes(image_path, output_width=128, output_height=64):
    """
    Converte uma imagem para byte array no formato do SSD1306.
    
    Args:
        image_path: Caminho para a imagem
        output_width: Largura desejada (padrão: 128)
        output_height: Altura desejada (padrão: 64)
    
    Returns:
        bytearray: Array de bytes representando a imagem
    """
    # Carrega e converte a imagem
    img = Image.open(image_path)
    
    # Redimensiona mantendo proporção e centraliza
    img.thumbnail((output_width, output_height), Image.Resampling.LANCZOS)
    
    # Cria imagem de destino
    final_img = Image.new("1", (output_width, output_height), 0)
    
    # Centraliza a imagem
    x_offset = (output_width - img.width) // 2
    y_offset = (output_height - img.height) // 2
    final_img.paste(img, (x_offset, y_offset))
    
    # Converte para modo "1" (monocromático)
    final_img = final_img.convert("1")
    
    # Converte para byte array no formato do SSD1306
    # Formato SSD1306: cada byte representa 8 pixels verticais consecutivos
    # Para cada coluna x, organizamos bytes verticalmente (LSB no topo)
    byte_array = bytearray()
    
    for x in range(output_width):
        for y_page in range(output_height // 8):  # 64 / 8 = 8 páginas
            byte_val = 0
            for bit in range(8):
                y = y_page * 8 + bit
                if y < output_height:
                    pixel = final_img.getpixel((x, y))
                    if pixel > 0:  # Pixel branco
                        byte_val |= (1 << bit)  # LSB primeiro (topo)
            byte_array.append(byte_val)
    
    return byte_array


def generate_logo_file(byte_array, output_path="logo_bitmap.py"):
    """Gera o arquivo logo_bitmap.py com o byte array."""
    content = '''"""
Arquivo para armazenar o bitmap da logo.
Este arquivo foi gerado automaticamente pelo script convert_logo.py
"""

# Array de bytes da logo (128x64 = 8192 bits = 1024 bytes)
# Formato: cada byte representa 8 pixels horizontais (MSB primeiro)
logo_bitmap_bytes = bytearray([
'''
    
    # Formata o byte array em linhas de 16 bytes
    for i in range(0, len(byte_array), 16):
        line_bytes = byte_array[i:i+16]
        hex_values = ', '.join(f'0x{b:02x}' for b in line_bytes)
        content += f'    {hex_values},\n'
    
    content += '])\n'
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Arquivo {output_path} gerado com sucesso!")
    print(f"  Tamanho: {len(byte_array)} bytes ({len(byte_array) * 8} pixels)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python convert_logo.py <caminho_da_imagem>")
        print("Exemplo: python convert_logo.py logo.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        print(f"Convertendo {image_path} para formato bitmap...")
        byte_array = image_to_bitmap_bytes(image_path)
        
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "logo_bitmap.py")
        
        generate_logo_file(byte_array, output_path)
        
    except Exception as e:
        print(f"Erro ao converter imagem: {e}")
        sys.exit(1)


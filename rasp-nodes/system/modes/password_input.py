"""
Modo de entrada de senha via roleta de caracteres.
Interface intuitiva com navegação por botões.
"""

from controllers.display import draw_password_roulette, draw_connecting, draw_success, draw_error
from controllers.buttons import read_button
import time

# Conjunto de caracteres disponíveis (ordem lógica)
# Inclui caracteres de ação: '<' (backspace) e múltiplos de confirmação (' ', '>', '=', '#')
CHARSET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "!@#$%&*()-_=+[]{}|;:',.<>?/\\ "
    "~`^\""
    "<>#="  # adiciona backspace '<' e confirmações extras '#', '>' e '='
)

# Conjuntos especiais para ações
SUBMIT_CHARS = {" ", ">", "=", "#"}
BACKSPACE_CHAR = "<"

def handle_password_input(ssid, on_connect_callback=None):
    """
    Função principal para entrada de senha (compatibilidade com código existente).
    
    Parâmetros:
    - ssid: Nome da rede WiFi
    - on_connect_callback: Função chamada ao tentar conectar (ssid, password)
    
    Retorna:
    - (success: bool, password: str ou None)
    """
    return password_input_mode(ssid, on_connect_callback)


def password_input_mode(ssid, on_connect_callback=None):
    """
    Modo de entrada de senha com navegação por roleta.
    
    Parâmetros:
    - ssid: Nome da rede WiFi
    - on_connect_callback: Função chamada ao tentar conectar (ssid, password)
    
    Retorna:
    - (success: bool, password: str ou None)
    """
    print(f"\n[Password Input] Iniciando modo de entrada de senha")
    print(f"[Password Input] SSID: '{ssid}'")
    print(f"[Password Input] Callback fornecido: {'Sim' if on_connect_callback else 'Não'}")
    
    password = ""
    cursor_pos = 0  # Posição na roleta de caracteres
    last_update = time.time()
    
    # Desenha interface inicial
    draw_password_roulette(ssid, password, CHARSET, cursor_pos)
    
    while True:
        # Lê botão
        button = read_button()
        
        if button:
            current_time = time.time()
            
            if button == 'left':
                # Navega para esquerda na roleta
                cursor_pos = (cursor_pos - 1) % len(CHARSET)
                draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                
            elif button == 'right':
                # Navega para direita na roleta
                cursor_pos = (cursor_pos + 1) % len(CHARSET)
                draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                
            elif button == 'ok':
                # Comportamentos diferentes dependendo do contexto
                current_char = CHARSET[cursor_pos]

                # Ação: backspace
                if current_char == BACKSPACE_CHAR:
                    if len(password) > 0:
                        password = password[:-1]
                        draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                    else:
                        return (False, None)
                    
                # Ação: confirmar (qualquer um dos SUBMIT_CHARS)
                elif current_char in SUBMIT_CHARS:
                    if len(password) == 0:
                        # Nada digitado → cancelar
                        print(f"[Password Input] Cancelado: senha vazia")
                        return (False, None)

                    # Confirma conexão
                    print(f"\n[Password Input] Senha confirmada para SSID '{ssid}'")
                    print(f"[Password Input] Tamanho da senha: {len(password)} caracteres")
                    draw_connecting(ssid)
                    
                    if on_connect_callback:
                        print(f"[Password Input] Chamando callback on_connect_callback...")
                        success, message = on_connect_callback(ssid, password)
                        print(f"[Password Input] Callback retornou: success={success}, message='{message}'")
                        
                        if success:
                            print(f"[Password Input] ✓ Conexão bem-sucedida!")
                            draw_success(ssid, message)
                            time.sleep(2)
                            return (True, password)
                        else:
                            print(f"[Password Input] ✗ Erro na conexão: {message}")
                            draw_error(message)
                            time.sleep(2)
                            # Volta para edição
                            draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                    else:
                        # Modo teste - sempre sucesso
                        print(f"[Password Input] Modo teste - sem callback, retornando sucesso")
                        return (True, password)

                # Senão, adiciona caractere à senha
                else:
                    password += current_char
                    draw_password_roulette(ssid, password, CHARSET, cursor_pos)
            
            last_update = current_time
        
        # Pequena pausa para não sobrecarregar CPU
        time.sleep(0.05)


def password_input_mode_backspace(ssid, on_connect_callback=None):
    """
    Modo alternativo com backspace explícito.
    Pressionar OK em espaço vazio = backspace.
    Pressionar OK duas vezes rápido = submeter senha.
    """
    password = ""
    cursor_pos = 0
    last_ok_press = 0
    double_click_threshold = 0.5  # 500ms para duplo clique
    
    draw_password_roulette(ssid, password, CHARSET, cursor_pos)
    
    while True:
        button = read_button()
        
        if button:
            current_time = time.time()
            
            if button == 'left':
                cursor_pos = (cursor_pos - 1) % len(CHARSET)
                draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                
            elif button == 'right':
                cursor_pos = (cursor_pos + 1) % len(CHARSET)
                draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                
            elif button == 'ok':
                current_char = CHARSET[cursor_pos]
                
                # Verifica duplo clique
                time_since_last_ok = current_time - last_ok_press
                
                if time_since_last_ok < double_click_threshold and len(password) > 0:
                    # Duplo clique = submeter senha
                    draw_connecting(ssid)
                    
                    if on_connect_callback:
                        success, message = on_connect_callback(ssid, password)
                        
                        if success:
                            draw_success(ssid, message)
                            time.sleep(2)
                            return (True, password)
                        else:
                            draw_error(message)
                            time.sleep(2)
                            draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                    else:
                        return (True, password)
                
                # Espaço vazio = backspace
                elif current_char == ' ' and len(password) > 0:
                    password = password[:-1]
                    draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                
                # Cancelar (espaço sem senha)
                elif current_char == ' ' and len(password) == 0:
                    return (False, None)
                
                # Adiciona caractere
                else:
                    password += current_char
                    draw_password_roulette(ssid, password, CHARSET, cursor_pos)
                
                last_ok_press = current_time
        
        time.sleep(0.05)


# Exemplo de uso
if __name__ == "__main__":
    def mock_connect(ssid, pwd):
        """Simula tentativa de conexão."""
        print(f"Conectando em '{ssid}' com senha '{pwd}'")
        time.sleep(1)
        
        # Simula sucesso se senha tem mais de 5 caracteres
        if len(pwd) >= 5:
            return (True, "192.168.1.100")
        else:
            return (False, "Senha muito curta")
    
    # Teste do modo principal
    success, password = handle_password_input("MinhaRedeWiFi", mock_connect)
    print(f"Resultado: success={success}, password='{password}'")

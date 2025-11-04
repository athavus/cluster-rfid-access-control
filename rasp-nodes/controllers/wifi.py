import subprocess
import re


def get_connected_ssid():
    """
    ----------------------------------------------------------------------
    @brief Retorna o SSID da rede Wi-Fi atualmente conectada.

    Obtem o nome (SSID) da rede ativa através do NetworkManager.
    Se não houver rede conectada, retorna uma string vazia.

    @return String com o SSID da rede atual ou "" se desconectado.
    ----------------------------------------------------------------------
    """
    try:
        cmd = "nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d: -f2"
        return subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""


def list_available_ssids():
    """
    ----------------------------------------------------------------------
    @brief Lista todos os SSIDs disponíveis nas proximidades.

    Força a revarredura (`rescan`) de redes Wi-Fi
    e retorna uma lista de nomes de SSIDs únicos detectados.

    @return Lista de strings contendo os SSIDs disponíveis.
    ----------------------------------------------------------------------
    """
    try:
        cmd = "sudo nmcli dev wifi rescan && sudo nmcli -t -f ssid dev wifi list"
        available_ssids = subprocess.check_output(cmd, shell=True).decode("utf-8").splitlines()

        valid_ssids = []
        for ssid in available_ssids:
            if ssid and ssid not in valid_ssids:
                valid_ssids.append(ssid)
    
        return valid_ssids
    except subprocess.CalledProcessError:
        return []


def get_wifi_security_type(ssid):
    """
    ----------------------------------------------------------------------
    @brief Detecta o tipo de segurança da rede WiFi (WPA2, WPA2 802.1X, etc).
    
    Analisa a saída do nmcli para determinar se a rede usa WPA2 normal
    ou WPA2 802.1X (Enterprise), que requer certificados adicionais.
    
    @param ssid: Nome da rede WiFi
    
    @return String com o tipo de segurança detectado ou 'WPA2' como padrão
    ----------------------------------------------------------------------
    """
    try:
        # Busca informações detalhadas da rede específica
        # O formato do nmcli é: SSID:SECURITY
        # Exemplo: "mentira:WPA2" ou "Embedded:WPA2 802.1X"
        cmd = f"nmcli -t -f SSID,SECURITY dev wifi list | grep -i '^{re.escape(ssid)}:'"
        result = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        
        if not result:
            # Se não encontrar, tenta sem o prefixo SSID (pode ser que o formato seja diferente)
            cmd = f"nmcli -t -f SSID,SECURITY dev wifi list | grep -i '{re.escape(ssid)}'"
            result = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        
        # Verifica se é 802.1X (Enterprise)
        if result and ('802.1X' in result or 'enterprise' in result.lower()):
            return '802.1X'
        
        # Se tem WPA2 ou WPA, assume WPA2 normal (pode conectar com senha)
        if result and ('WPA2' in result or 'WPA' in result):
            return 'WPA2'
        
        # Padrão: assume WPA2 (mais comum)
        return 'WPA2'
        
    except subprocess.CalledProcessError:
        # Se der erro, assume WPA2 normal (mais seguro que retornar erro)
        return 'WPA2'
    except Exception:
        return 'WPA2'


def known_connections():
    """
    ----------------------------------------------------------------------
    @brief Obtém a lista de conexões Wi-Fi conhecidas pelo sistema.

    Usa o comando `nmcli -t -f NAME connection show` para retornar
    as conexões salvas previamente no NetworkManager.

    @return Lista de nomes de conexões conhecidas.
    ----------------------------------------------------------------------
    """
    try:
        cmd = "nmcli -t -f NAME connection show"
        result = subprocess.check_output(cmd, shell=True).decode("utf-8").splitlines()
    
        cleaned_lines = []
        for line in result:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)

        return cleaned_lines
    except subprocess.CalledProcessError:
        return []


def connect_to_wifi(ssid, password):
    """
    ----------------------------------------------------------------------
    @brief Conecta a um ponto de acesso Wi-Fi.

    Se o SSID já for conhecido (salvo anteriormente), tenta reconectar usando
    `nmcli con up`. Caso contrário, cria uma nova conexão com senha.
    
    Esta função especifica explicitamente o tipo de autenticação (key-mgmt)
    para evitar erros com versões mais recentes do NetworkManager, especialmente
    o erro "802-11-wireless-security.key-mgmt: property is missing".

    @param ssid: Nome da rede Wi-Fi.
    @param password: Senha da rede Wi-Fi.

    @return True se a conexão foi bem-sucedida, False em caso de erro.
    ----------------------------------------------------------------------
    """
    try:
        # Se já existe conexão conhecida, apenas ativa
        if ssid in known_connections():
            cmd = f"sudo nmcli con up '{ssid}'"
            subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
            return True
        
        # Detecta o tipo de segurança da rede
        security_type = get_wifi_security_type(ssid)
        
        # Para redes 802.1X (Enterprise), não podemos conectar apenas com senha
        # Essas redes requerem certificado/credenciais adicionais
        if security_type == '802.1X':
            return False
        
        # Método preferido: cria conexão usando 'connection add' com todas as propriedades
        # Isso especifica explicitamente o key-mgmt, resolvendo o problema
        try:
            # Remove conexão existente se houver (para evitar conflitos)
            subprocess.run(
                f"sudo nmcli con delete '{ssid}'",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
        except:
            pass  # Ignora se não existir ou der erro
        
        # Cria nova conexão especificando explicitamente wifi-sec.key-mgmt wpa-psk
        # Isso resolve o erro "key-mgmt: property is missing" em versões recentes do NetworkManager
        cmd = (
            f"sudo nmcli connection add "
            f"type wifi "
            f"con-name '{ssid}' "
            f"ssid '{ssid}' "
            f"wifi-sec.key-mgmt wpa-psk "
            f"wifi-sec.psk '{password}'"
        )
        subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=10)
        
        # Ativa a conexão criada
        cmd = f"sudo nmcli con up '{ssid}'"
        subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
        
        return True
        
    except subprocess.CalledProcessError:
        # Se falhar com o método principal, tenta método alternativo
        try:
            # Método alternativo: usa dev wifi connect mas especificando key-mgmt
            # Escapa caracteres especiais no SSID e senha para evitar problemas
            ssid_escaped = ssid.replace("'", "'\"'\"'")
            password_escaped = password.replace("'", "'\"'\"'")
            
            cmd = (
                f"sudo nmcli dev wifi connect '{ssid_escaped}' "
                f"password '{password_escaped}' "
                f"wifi-sec.key-mgmt wpa-psk"
            )
            subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=30)
            return True
        except:
            return False
    except Exception:
        return False


def get_network_info():
    """
    ----------------------------------------------------------------------
    @brief Coleta informações detalhadas sobre o estado da rede e do sistema.

    Retorna um dicionário contendo:
      - HOST: Nome do host do sistema.
      - IP: Endereço IP local.
      - WIFI: Força do sinal e taxa de transmissão da conexão Wi-Fi.
      - SSH: Status do serviço SSH (ativo/inativo).
      - USERS: Quantidade de usuários conectados via SSH.
      - SSID: Nome da rede Wi-Fi atual.

    @return Dicionário com informações sobre o estado da rede.
    ----------------------------------------------------------------------
    """
    info = {}

    # Nome do host
    cmd = "hostname"
    info["HOST"] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

    # Endereço IP
    cmd = "hostname -I | cut -d' ' -f1"
    info["IP"] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

    # Informações de sinal Wi-Fi
    try:
        cmd = "iw dev wlan0 link | awk '/signal/ {sig=$2} /tx bitrate/ {rate=$3; printf \"%sdbm|%smbit/s\", sig, rate}'"
        info["WIFI"] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        info["WIFI"] = "DESCONECTADO"

    # Status do SSH
    cmd = "systemctl is-active ssh"
    info["SSH"] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

    # Número de usuários conectados via SSH
    cmd = "who | grep ssh | wc -l"
    info["USERS"] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

    # SSID atual
    info["SSID"] = get_connected_ssid()

    return info

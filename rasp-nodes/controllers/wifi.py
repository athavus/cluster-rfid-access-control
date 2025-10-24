import subprocess

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

    @param ssid: Nome da rede Wi-Fi.
    @param password: Senha da rede Wi-Fi.

    @return True se a conexão foi bem-sucedida, False em caso de erro.
    ----------------------------------------------------------------------
    """
    try:
        if ssid in known_connections():
            cmd = f"sudo nmcli con up '{ssid}'"
        else:
            cmd = f"sudo nmcli dev wifi connect '{ssid}' password '{password}'"
        subprocess.check_output(cmd, shell=True)

        return True
    except subprocess.CalledProcessError:
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

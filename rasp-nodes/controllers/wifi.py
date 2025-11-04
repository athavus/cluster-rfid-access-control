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
    
    A função aguarda a conexão ser estabelecida e verifica o status antes de retornar.

    @param ssid: Nome da rede Wi-Fi.
    @param password: Senha da rede Wi-Fi.

    @return True se a conexão foi bem-sucedida, False em caso de erro.
    ----------------------------------------------------------------------
    """
    import time
    import shlex
    
    print(f"\n[WiFi] Iniciando conexão à rede: '{ssid}'")
    print(f"[WiFi] Senha fornecida: {'Sim (***)' if password and password.strip() else 'Não'}")
    
    # Validação básica
    if not ssid or not ssid.strip():
        print("[WiFi] ERRO: SSID vazio ou inválido!")
        return False
    
    try:
        known_conns = known_connections()
        print(f"[WiFi] Conexões conhecidas: {known_conns}")
        
        # Se já existe conexão conhecida, apenas ativa
        if ssid in known_conns:
            print(f"[WiFi] Rede '{ssid}' já conhecida, tentando reconectar...")
            # Usa shlex.quote para escape seguro de caracteres especiais
            ssid_quoted = shlex.quote(ssid)
            cmd = f"sudo nmcli con up {ssid_quoted}"
            print(f"[WiFi] Comando: {cmd}")
            try:
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=30)
                print(f"[WiFi] Comando executado com sucesso. Aguardando conexão...")
                # Aguarda mais tempo para conexão estabelecer
                time.sleep(5)
                # Verifica múltiplas vezes
                for check in range(10):
                    connected_ssid = get_connected_ssid()
                    print(f"[WiFi] Verificação {check+1}/10: SSID conectado = '{connected_ssid}'")
                    if connected_ssid == ssid:
                        print(f"[WiFi] ✓ Conexão estabelecida com sucesso (método: conexão conhecida)")
                        return True
                    time.sleep(1)
                print(f"[WiFi] Falhou ao reconectar rede conhecida, tentando criar nova conexão...")
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
                print(f"[WiFi] ERRO ao reconectar rede conhecida: {error_msg}")
            except Exception as e:
                print(f"[WiFi] EXCEÇÃO ao reconectar rede conhecida: {e}")
            # Se falhou, continua para recriar a conexão
        
        # Detecta o tipo de segurança da rede
        print(f"[WiFi] Detectando tipo de segurança da rede...")
        security_type = get_wifi_security_type(ssid)
        print(f"[WiFi] Tipo de segurança detectado: {security_type}")
        
        # Para redes 802.1X (Enterprise), não podemos conectar apenas com senha
        # Essas redes requerem certificado/credenciais adicionais
        if security_type == '802.1X':
            print(f"[WiFi] ERRO: Rede 802.1X (Enterprise) requer certificados adicionais, não é possível conectar apenas com senha")
            return False
        
        # Se não tem senha e não é conhecida, retorna False
        if not password or not password.strip():
            print(f"[WiFi] ERRO: Senha não fornecida e rede não é conhecida")
            return False
        
        # Remove conexão existente se houver (para evitar conflitos)
        print(f"[WiFi] Removendo conexão existente se houver...")
        try:
            ssid_quoted = shlex.quote(ssid)
            cmd = f"sudo nmcli con delete {ssid_quoted}"
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                print(f"[WiFi] Conexão existente removida com sucesso")
            else:
                print(f"[WiFi] Nenhuma conexão existente para remover (ou erro: {result.stderr.decode('utf-8')})")
            time.sleep(1)  # Pausa maior após deletar
        except Exception as e:
            print(f"[WiFi] Aviso ao tentar remover conexão existente: {e}")
        
        # Método 1: Tenta criar conexão e depois ativar (mais confiável)
        print(f"[WiFi] === MÉTODO 1: Criar conexão e depois ativar ===")
        try:
            # Usa shlex.quote para escape seguro (inclui espaços e caracteres especiais)
            ssid_quoted = shlex.quote(ssid)
            password_quoted = shlex.quote(password)
            
            print(f"[WiFi] SSID escapado: {ssid_quoted}")
            print(f"[WiFi] Criando nova conexão...")
            
            # Cria nova conexão usando connection add com sintaxe correta
            # Usa 802-11-wireless-security.psk ao invés de wifi-sec.psk para garantir compatibilidade
            cmd = (
                f"sudo nmcli connection add "
                f"type wifi "
                f"con-name {ssid_quoted} "
                f"ifname '*' "
                f"ssid {ssid_quoted} "
                f"802-11-wireless-security.key-mgmt wpa-psk "
                f"802-11-wireless-security.psk {password_quoted}"
            )
            print(f"[WiFi] Comando criar conexão: {cmd[:100]}... (senha oculta)")
            
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=15)
            print(f"[WiFi] ✓ Conexão criada com sucesso")
            print(f"[WiFi] Resultado: {result.decode('utf-8') if result else 'N/A'}")
            
            # Aguarda antes de tentar ativar
            print(f"[WiFi] Aguardando 2 segundos antes de ativar...")
            time.sleep(2)
            
            # Ativa a conexão criada
            cmd = f"sudo nmcli con up {ssid_quoted}"
            print(f"[WiFi] Ativando conexão: {cmd}")
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=45)
            print(f"[WiFi] ✓ Comando de ativação executado")
            print(f"[WiFi] Resultado: {result.decode('utf-8') if result else 'N/A'}")
            
            # Aguarda a conexão ser estabelecida (aumentado tempo de espera)
            # Redes podem levar mais tempo, especialmente com senha incorreta
            print(f"[WiFi] Aguardando conexão ser estabelecida (até 25 segundos)...")
            for attempt in range(25):  # Aumentado para 25 segundos
                time.sleep(1)
                connected_ssid = get_connected_ssid()
                print(f"[WiFi] Tentativa {attempt+1}/25: SSID conectado = '{connected_ssid}'")
                if connected_ssid == ssid:
                    print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 1) ✓✓✓")
                    return True
            
            # Verificação adicional após esperar mais
            print(f"[WiFi] Verificação adicional final (aguardando mais 5 segundos)...")
            time.sleep(5)
            final_ssid = get_connected_ssid()
            print(f"[WiFi] SSID final após verificação adicional: '{final_ssid}'")
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 1, verificação adicional) ✓✓✓")
                return True
            
            print(f"[WiFi] ✗ Método 1 falhou: não conseguiu conectar após todas as tentativas")
            print(f"[WiFi] SSID esperado: '{ssid}', SSID atual: '{final_ssid}'")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"[WiFi] ✗ ERRO no Método 1: {error_msg}")
            print(f"[WiFi] Código de retorno: {e.returncode}")
        except Exception as e:
            print(f"[WiFi] ✗ EXCEÇÃO no Método 1: {e}")
            import traceback
            print(f"[WiFi] Traceback: {traceback.format_exc()}")
        
        # Método 2: Tenta criar conexão sem senha e depois modificar com senha
        print(f"[WiFi] === MÉTODO 2: Criar conexão e modificar com senha ===")
        try:
            ssid_quoted = shlex.quote(ssid)
            password_quoted = shlex.quote(password)
            
            # Primeiro cria conexão sem senha
            print(f"[WiFi] Criando conexão sem senha inicialmente...")
            cmd = (
                f"sudo nmcli connection add "
                f"type wifi "
                f"con-name {ssid_quoted} "
                f"ifname '*' "
                f"ssid {ssid_quoted}"
            )
            print(f"[WiFi] Comando: {cmd}")
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=15)
            print(f"[WiFi] ✓ Conexão criada")
            
            # Agora modifica para adicionar segurança e senha
            print(f"[WiFi] Adicionando segurança WPA-PSK e senha...")
            cmd = (
                f"sudo nmcli connection modify {ssid_quoted} "
                f"802-11-wireless-security.key-mgmt wpa-psk "
                f"802-11-wireless-security.psk {password_quoted}"
            )
            print(f"[WiFi] Comando modificar: {cmd[:100]}... (senha oculta)")
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=15)
            print(f"[WiFi] ✓ Segurança e senha adicionadas")
            
            time.sleep(2)
            
            # Ativa a conexão
            cmd = f"sudo nmcli con up {ssid_quoted}"
            print(f"[WiFi] Ativando conexão: {cmd}")
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=45)
            print(f"[WiFi] ✓ Comando de ativação executado")
            
            # Aguarda conexão
            print(f"[WiFi] Aguardando conexão ser estabelecida (até 25 segundos)...")
            for attempt in range(25):
                time.sleep(1)
                connected_ssid = get_connected_ssid()
                print(f"[WiFi] Tentativa {attempt+1}/25: SSID conectado = '{connected_ssid}'")
                if connected_ssid == ssid:
                    print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 2) ✓✓✓")
                    return True
            
            time.sleep(5)
            final_ssid = get_connected_ssid()
            print(f"[WiFi] SSID final: '{final_ssid}'")
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 2, verificação adicional) ✓✓✓")
                return True
            
            print(f"[WiFi] ✗ Método 2 falhou")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"[WiFi] ✗ ERRO no Método 2: {error_msg}")
            print(f"[WiFi] Código de retorno: {e.returncode}")
        except Exception as e:
            print(f"[WiFi] ✗ EXCEÇÃO no Método 2: {e}")
            import traceback
            print(f"[WiFi] Traceback: {traceback.format_exc()}")
        
        # Método 3: Última tentativa - usa dev wifi connect (método mais direto)
        print(f"[WiFi] === MÉTODO 3: Conexão direta (dev wifi connect) ===")
        try:
            # Usa shlex.quote para escape seguro
            ssid_quoted = shlex.quote(ssid)
            password_quoted = shlex.quote(password)
            
            # Tenta conectar diretamente usando dev wifi connect
            # O comando dev wifi connect não aceita wifi-sec.key-mgmt como argumento separado
            cmd = (
                f"sudo nmcli dev wifi connect {ssid_quoted} "
                f"password {password_quoted}"
            )
            print(f"[WiFi] Comando conexão direta: {cmd[:100]}... (senha oculta)")
            
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=45)
            print(f"[WiFi] ✓ Comando de conexão direta executado")
            print(f"[WiFi] Resultado: {result.decode('utf-8') if result else 'N/A'}")
            
            # Aguarda a conexão ser estabelecida com mais tempo
            print(f"[WiFi] Aguardando conexão ser estabelecida (até 25 segundos)...")
            for attempt in range(25):
                time.sleep(1)
                connected_ssid = get_connected_ssid()
                print(f"[WiFi] Tentativa {attempt+1}/25: SSID conectado = '{connected_ssid}'")
                if connected_ssid == ssid:
                    print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 3) ✓✓✓")
                    return True
            
            # Verificação adicional
            print(f"[WiFi] Verificação adicional final (aguardando mais 5 segundos)...")
            time.sleep(5)
            final_ssid = get_connected_ssid()
            print(f"[WiFi] SSID final após verificação adicional: '{final_ssid}'")
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 3, verificação adicional) ✓✓✓")
                return True
            
            print(f"[WiFi] ✗ Método 3 falhou: não conseguiu conectar após todas as tentativas")
            print(f"[WiFi] SSID esperado: '{ssid}', SSID atual: '{final_ssid}'")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"[WiFi] ✗ ERRO no Método 3: {error_msg}")
            print(f"[WiFi] Código de retorno: {e.returncode}")
        except Exception as e:
            print(f"[WiFi] ✗ EXCEÇÃO no Método 3: {e}")
            import traceback
            print(f"[WiFi] Traceback: {traceback.format_exc()}")
        
        # Se todos os métodos falharam, retorna False
        print(f"[WiFi] ✗✗✗ TODOS OS MÉTODOS FALHARAM ✗✗✗")
        print(f"[WiFi] Verificando status final da conexão...")
        final_ssid = get_connected_ssid()
        print(f"[WiFi] SSID final do sistema: '{final_ssid}'")
        print(f"[WiFi] Status do NetworkManager:")
        try:
            status = subprocess.check_output("sudo nmcli connection show --active", shell=True, stderr=subprocess.PIPE, timeout=5)
            print(f"[WiFi] {status.decode('utf-8')}")
        except:
            print(f"[WiFi] Não foi possível verificar status do NetworkManager")
        
        return False
        
    except Exception as e:
        print(f"[WiFi] ✗✗✗ EXCEÇÃO CRÍTICA: {e} ✗✗✗")
        import traceback
        print(f"[WiFi] Traceback completo: {traceback.format_exc()}")
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

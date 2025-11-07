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
        
        # Se já existe conexão conhecida E não temos senha para fornecer, tenta apenas ativar
        if ssid in known_conns and (not password or not password.strip()):
            print(f"[WiFi] Rede '{ssid}' já conhecida e sem senha fornecida, tentando reconectar...")
            ssid_quoted = shlex.quote(ssid)
            cmd = f"sudo nmcli con up {ssid_quoted}"
            print(f"[WiFi] Comando: {cmd}")
            try:
                result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=30)
                print(f"[WiFi] Comando executado com sucesso. Aguardando conexão...")
                time.sleep(5)
                for check in range(10):
                    connected_ssid = get_connected_ssid()
                    print(f"[WiFi] Verificação {check+1}/10: SSID conectado = '{connected_ssid}'")
                    if connected_ssid == ssid:
                        print(f"[WiFi] ✓ Conexão estabelecida com sucesso (método: conexão conhecida)")
                        return True
                    time.sleep(1)
                print(f"[WiFi] Falhou ao reconectar rede conhecida, continuando...")
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
                print(f"[WiFi] ERRO ao reconectar rede conhecida: {error_msg}")
                # Se detectar erro 802.11, reinicia o NetworkManager
                if '802.11' in error_msg or '802-11' in error_msg:
                    print(f"[WiFi] Erro 802.11 detectado, reiniciando NetworkManager...")
                    try:
                        subprocess.check_output("sudo systemctl restart NetworkManager", shell=True, timeout=10)
                        print(f"[WiFi] NetworkManager reiniciado com sucesso")
                        time.sleep(2)  # Aguarda o NetworkManager reiniciar
                    except Exception as restart_err:
                        print(f"[WiFi] Erro ao reiniciar NetworkManager: {restart_err}")
                # Se o erro indica que precisa de senha, continua para recriar
                if "password" in error_msg.lower() or "secret" in error_msg.lower() or "not provided" in error_msg.lower():
                    print(f"[WiFi] Conexão conhecida precisa de senha, recriando...")
            except Exception as e:
                print(f"[WiFi] EXCEÇÃO ao reconectar rede conhecida: {e}")
            # Continua para recriar se falhou
        
        # Se temos senha OU a conexão conhecida falhou, sempre recria a conexão para garantir senha correta
        if password and password.strip():
            print(f"[WiFi] Senha fornecida, recriando conexão para garantir configuração correta...")
        elif ssid in known_conns:
            print(f"[WiFi] Rede conhecida, mas sem senha - tentando conectar sem recriar primeiro...")
        
        # Detecta o tipo de segurança da rede
        print(f"[WiFi] Detectando tipo de segurança da rede...")
        security_type = get_wifi_security_type(ssid)
        print(f"[WiFi] Tipo de segurança detectado: {security_type}")
        
        # Para redes 802.1X (Enterprise), não podemos conectar apenas com senha
        if security_type == '802.1X':
            print(f"[WiFi] ERRO: Rede 802.1X (Enterprise) requer certificados adicionais")
            return False
        
        # Se não tem senha e não conseguiu conectar como conhecida, retorna False
        if not password or not password.strip():
            if ssid not in known_conns:
                print(f"[WiFi] ERRO: Senha não fornecida e rede não é conhecida")
                return False
            else:
                print(f"[WiFi] AVISO: Rede conhecida mas falhou ao conectar sem senha")
                return False
        
        # Se temos senha, sempre remove e recria para garantir configuração correta
        print(f"[WiFi] Removendo conexão existente se houver...")
        ssid_quoted = shlex.quote(ssid)
        for attempt in range(3):  # Tenta remover até 3 vezes
            try:
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
                    break
                else:
                    stderr_msg = result.stderr.decode('utf-8')
                    if "unknown connection" not in stderr_msg.lower():
                        print(f"[WiFi] Erro ao remover: {stderr_msg}")
                    # Se for "unknown connection", está OK, não existe
                    break
            except Exception as e:
                print(f"[WiFi] Aviso ao tentar remover (tentativa {attempt+1}): {e}")
                if attempt < 2:
                    time.sleep(0.5)
        
        time.sleep(1)  # Pausa após deletar
        
        # Método 1: Usa dev wifi connect (método mais direto e confiável)
        print(f"[WiFi] === MÉTODO 1: Conexão direta (dev wifi connect) ===")
        try:
            ssid_quoted = shlex.quote(ssid)
            password_quoted = shlex.quote(password)
            
            # Este método cria a conexão e conecta em um único comando
            cmd = f"sudo nmcli dev wifi connect {ssid_quoted} password {password_quoted}"
            print(f"[WiFi] Comando: {cmd[:80]}... (senha oculta)")
            print(f"[WiFi] Executando conexão direta...")
            
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=45)
            print(f"[WiFi] ✓ Comando executado com sucesso")
            print(f"[WiFi] Resultado: {result.decode('utf-8').strip() if result else 'N/A'}")
            
            # Aguarda a conexão ser estabelecida
            print(f"[WiFi] Aguardando conexão ser estabelecida (até 30 segundos)...")
            for attempt in range(30):
                time.sleep(1)
                connected_ssid = get_connected_ssid()
                if attempt % 5 == 0 or connected_ssid == ssid:  # Log a cada 5 segundos
                    print(f"[WiFi] Tentativa {attempt+1}/30: SSID conectado = '{connected_ssid}'")
                if connected_ssid == ssid:
                    print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 1) ✓✓✓")
                    return True
            
            # Verificação adicional
            time.sleep(5)
            final_ssid = get_connected_ssid()
            print(f"[WiFi] SSID final: '{final_ssid}'")
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 1, verificação adicional) ✓✓✓")
                return True
            
            print(f"[WiFi] ✗ Método 1 falhou: SSID esperado '{ssid}', atual '{final_ssid}'")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"[WiFi] ✗ ERRO no Método 1: {error_msg}")
            print(f"[WiFi] Código de retorno: {e.returncode}")
            # Se detectar erro 802.11, reinicia o NetworkManager
            if '802.11' in error_msg or '802-11' in error_msg:
                print(f"[WiFi] Erro 802.11 detectado, reiniciando NetworkManager...")
                try:
                    subprocess.check_output("sudo systemctl restart NetworkManager", shell=True, timeout=10)
                    print(f"[WiFi] NetworkManager reiniciado com sucesso")
                    time.sleep(2)  # Aguarda o NetworkManager reiniciar
                except Exception as restart_err:
                    print(f"[WiFi] Erro ao reiniciar NetworkManager: {restart_err}")
        except Exception as e:
            print(f"[WiFi] ✗ EXCEÇÃO no Método 1: {e}")
            import traceback
            print(f"[WiFi] Traceback: {traceback.format_exc()}")
        
        # Método 2: Cria conexão completa de uma vez e depois ativa
        print(f"[WiFi] === MÉTODO 2: Criar conexão completa e depois ativar ===")
        try:
            ssid_quoted = shlex.quote(ssid)
            password_quoted = shlex.quote(password)
            
            # Cria conexão com todas as configurações de uma vez
            cmd = (
                f"sudo nmcli connection add "
                f"type wifi "
                f"con-name {ssid_quoted} "
                f"ifname '*' "
                f"ssid {ssid_quoted} "
                f"802-11-wireless-security.key-mgmt wpa-psk "
                f"802-11-wireless-security.psk {password_quoted}"
            )
            print(f"[WiFi] Criando conexão completa: {cmd[:80]}... (senha oculta)")
            
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=15)
            print(f"[WiFi] ✓ Conexão criada: {result.decode('utf-8').strip() if result else 'N/A'}")
            
            time.sleep(2)
            
            # Ativa a conexão
            cmd = f"sudo nmcli con up {ssid_quoted}"
            print(f"[WiFi] Ativando conexão: {cmd}")
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=45)
            print(f"[WiFi] ✓ Comando de ativação executado")
            
            # Aguarda conexão
            print(f"[WiFi] Aguardando conexão (até 30 segundos)...")
            for attempt in range(30):
                time.sleep(1)
                connected_ssid = get_connected_ssid()
                if attempt % 5 == 0 or connected_ssid == ssid:
                    print(f"[WiFi] Tentativa {attempt+1}/30: SSID = '{connected_ssid}'")
                if connected_ssid == ssid:
                    print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 2) ✓✓✓")
                    return True
            
            time.sleep(5)
            final_ssid = get_connected_ssid()
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 2, verificação adicional) ✓✓✓")
                return True
            
            print(f"[WiFi] ✗ Método 2 falhou")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            print(f"[WiFi] ✗ ERRO no Método 2: {error_msg}")
            print(f"[WiFi] Código: {e.returncode}")
            # Se detectar erro 802.11, reinicia o NetworkManager
            if '802.11' in error_msg or '802-11' in error_msg:
                print(f"[WiFi] Erro 802.11 detectado, reiniciando NetworkManager...")
                try:
                    subprocess.check_output("sudo systemctl restart NetworkManager", shell=True, timeout=10)
                    print(f"[WiFi] NetworkManager reiniciado com sucesso")
                    time.sleep(2)  # Aguarda o NetworkManager reiniciar
                except Exception as restart_err:
                    print(f"[WiFi] Erro ao reiniciar NetworkManager: {restart_err}")
        except Exception as e:
            print(f"[WiFi] ✗ EXCEÇÃO no Método 2: {e}")
        
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
      - FRONTEND_PORT: Porta do frontend (padrão 5173 para Vite).

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

    # Porta do frontend (padrão 5173 para Vite)
    # Tenta detectar se há processo Vite/node rodando e qual porta está usando
    frontend_port = "5173"  # Porta padrão do Vite
    try:
        # Tenta múltiplas formas de detectar a porta do frontend
        # Método 1: Verifica processos node/vite e suas portas
        cmd = "ps aux | grep -E '(vite|node.*dev)' | grep -v grep | head -1"
        ps_result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=2).decode("utf-8").strip()
        if ps_result:
            # Método 2: Usa ss ou netstat para encontrar portas em uso (5173, 3000, 8080, etc)
            for port_candidate in ["5173", "3000", "8080", "5174", "5175"]:
                try:
                    # Tenta com ss primeiro (mais moderno)
                    cmd = f"ss -tlnp 2>/dev/null | grep ':{port_candidate}' | head -1"
                    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                    if result:
                        frontend_port = port_candidate
                        break
                except:
                    try:
                        # Fallback para netstat
                        cmd = f"netstat -tlnp 2>/dev/null | grep ':{port_candidate}' | head -1"
                        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                        if result:
                            frontend_port = port_candidate
                            break
                    except:
                        continue
    except:
        pass  # Se não conseguir detectar, usa o padrão 5173
    
    info["FRONTEND_PORT"] = frontend_port

    return info

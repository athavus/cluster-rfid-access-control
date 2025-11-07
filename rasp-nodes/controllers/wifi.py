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
                        # Limpa portas zumbis após mudança de rede
                        time.sleep(1)
                        cleanup_zombie_ports_on_network_change()
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
                    # Limpa portas zumbis após mudança de rede
                    time.sleep(1)
                    cleanup_zombie_ports_on_network_change()
                    return True
            
            # Verificação adicional
            time.sleep(5)
            final_ssid = get_connected_ssid()
            print(f"[WiFi] SSID final: '{final_ssid}'")
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 1, verificação adicional) ✓✓✓")
                # Limpa portas zumbis após mudança de rede
                time.sleep(1)
                cleanup_zombie_ports_on_network_change()
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
                    # Limpa portas zumbis após mudança de rede
                    time.sleep(1)
                    cleanup_zombie_ports_on_network_change()
                    return True
            
            time.sleep(5)
            final_ssid = get_connected_ssid()
            if final_ssid == ssid:
                print(f"[WiFi] ✓✓✓ CONEXÃO ESTABELECIDA COM SUCESSO (método 2, verificação adicional) ✓✓✓")
                # Limpa portas zumbis após mudança de rede
                time.sleep(1)
                cleanup_zombie_ports_on_network_change()
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


def detect_frontend_port():
    """
    ----------------------------------------------------------------------
    @brief Detecta a porta do frontend (npm/vite) ativo de forma inteligente.
    
    Varre processos node/vite ativos e identifica qual porta está realmente
    sendo usada. Se encontrar múltiplas portas, prioriza a mais recente.
    Também limpa portas zumbis de processos antigos.
    
    @return String com o número da porta (padrão "5173" se não encontrar)
    ----------------------------------------------------------------------
    """
    import time
    
    frontend_port = "5173"  # Porta padrão do Vite
    active_ports = []
    
    try:
        # Método 1: Encontra processos node/vite ativos e seus PIDs
        cmd = "ps aux | grep -E '(vite|node.*dev|npm.*dev)' | grep -v grep"
        ps_result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=2).decode("utf-8").strip()
        
        if ps_result:
            pids = []
            for line in ps_result.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            pids.append(pid)
                        except:
                            pass
            
            # Método 2: Para cada PID, verifica qual porta está usando com lsof
            for pid in pids:
                try:
                    # lsof mostra portas TCP abertas pelo processo
                    cmd = f"lsof -Pan -p {pid} -iTCP -sTCP:LISTEN 2>/dev/null | grep LISTEN"
                    lsof_result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                    if lsof_result:
                        # Extrai a porta da saída do lsof (formato: node 1234 user 23u IPv4 ... TCP *:5173 (LISTEN))
                        import re
                        port_match = re.search(r':(\d+)\s+\(LISTEN\)', lsof_result)
                        if port_match:
                            port = port_match.group(1)
                            # Verifica se é uma porta válida de frontend (5173, 3000, 8080, etc)
                            if port.isdigit() and int(port) >= 3000 and int(port) <= 65535:
                                # Pega o tempo de início do processo para priorizar o mais recente
                                try:
                                    cmd = f"ps -o lstart= -p {pid} 2>/dev/null"
                                    start_time = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                                    active_ports.append((port, pid, start_time))
                                except:
                                    active_ports.append((port, pid, ""))
                except:
                    continue
            
            # Se não encontrou com lsof, tenta método alternativo: verifica todas as portas comuns
            if not active_ports:
                for port_candidate in ["5173", "5174", "5175", "3000", "8080", "5176", "5177"]:
                    try:
                        # Verifica se a porta está em LISTEN e qual PID está usando
                        cmd = f"ss -tlnp 2>/dev/null | grep ':{port_candidate}' | grep LISTEN"
                        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                        if result:
                            # Extrai PID da saída do ss
                            import re
                            pid_match = re.search(r'pid=(\d+)', result)
                            if pid_match:
                                pid = int(pid_match.group(1))
                                # Verifica se é processo node/vite
                                try:
                                    cmd = f"ps -p {pid} -o comm= 2>/dev/null"
                                    proc_name = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                                    if 'node' in proc_name.lower() or 'vite' in proc_name.lower():
                                        active_ports.append((port_candidate, pid, ""))
                                except:
                                    pass
                    except:
                        continue
            
            # Se encontrou portas ativas, escolhe a mais recente ou a primeira
            if active_ports:
                # Ordena por tempo de início (mais recente primeiro) ou usa a primeira
                if len(active_ports) > 1:
                    # Se tem múltiplas portas, verifica se alguma é zumbi (processo antigo sem conexões)
                    valid_ports = []
                    for port, pid, start_time in active_ports:
                        try:
                            # Verifica se o processo ainda está respondendo (tem conexões ativas ou está em LISTEN recente)
                            cmd = f"ss -tnp 2>/dev/null | grep ':{port}' | wc -l"
                            conn_count = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                            # Se tem conexões ou está em LISTEN, é válido
                            if conn_count.isdigit() and int(conn_count) >= 0:
                                valid_ports.append((port, pid))
                        except:
                            valid_ports.append((port, pid))
                    
                    if valid_ports:
                        # Prioriza porta 5173 se disponível, senão usa a primeira válida
                        for port, pid in valid_ports:
                            if port == "5173":
                                frontend_port = port
                                break
                        else:
                            frontend_port = valid_ports[0][0]
                    else:
                        frontend_port = active_ports[0][0]
                else:
                    frontend_port = active_ports[0][0]
                
                # Limpa portas zumbis (outras portas que não são a ativa)
                if len(active_ports) > 1:
                    cleanup_zombie_ports(frontend_port, [p[0] for p in active_ports])
        
        # Se não encontrou processos, verifica se há alguma porta em LISTEN que possa ser frontend
        if frontend_port == "5173" and not active_ports:
            for port_candidate in ["5173", "5174", "5175", "3000", "8080"]:
                try:
                    cmd = f"ss -tlnp 2>/dev/null | grep ':{port_candidate}' | grep LISTEN"
                    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                    if result:
                        frontend_port = port_candidate
                        break
                except:
                    continue
                    
    except Exception as e:
        print(f"[WiFi] Aviso ao detectar porta do frontend: {e}")
    
    return frontend_port


def cleanup_zombie_ports_on_network_change():
    """
    ----------------------------------------------------------------------
    @brief Limpa portas zumbis quando há mudança de rede.
    
    Encontra processos node/vite ativos e identifica qual porta está realmente
    sendo usada. Mata processos em outras portas que são zumbis de conexões antigas.
    ----------------------------------------------------------------------
    """
    try:
        import re
        
        # Encontra todos os processos node/vite ativos e suas portas
        active_ports_pids = {}
        
        # Método 1: Encontra processos e suas portas via lsof
        try:
            cmd = "ps aux | grep -E '(vite|node.*dev|npm.*dev)' | grep -v grep"
            ps_result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=2).decode("utf-8").strip()
            
            if ps_result:
                pids = []
                for line in ps_result.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                pid = int(parts[1])
                                pids.append(pid)
                            except:
                                pass
                
                # Para cada PID, encontra a porta
                for pid in pids:
                    try:
                        cmd = f"lsof -Pan -p {pid} -iTCP -sTCP:LISTEN 2>/dev/null | grep LISTEN"
                        lsof_result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                        if lsof_result:
                            port_match = re.search(r':(\d+)\s+\(LISTEN\)', lsof_result)
                            if port_match:
                                port = port_match.group(1)
                                if port.isdigit() and int(port) >= 3000 and int(port) <= 65535:
                                    active_ports_pids[port] = pid
                    except:
                        continue
        except:
            pass
        
        # Método 2: Se não encontrou com lsof, usa ss para encontrar portas node/vite
        if not active_ports_pids:
            for port_candidate in ["5173", "5174", "5175", "5176", "5177", "3000", "8080"]:
                try:
                    cmd = f"ss -tlnp 2>/dev/null | grep ':{port_candidate}' | grep LISTEN"
                    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                    if result:
                        pid_match = re.search(r'pid=(\d+)', result)
                        if pid_match:
                            pid = int(pid_match.group(1))
                            try:
                                cmd = f"ps -p {pid} -o comm= 2>/dev/null"
                                proc_name = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                                if 'node' in proc_name.lower() or 'vite' in proc_name.lower():
                                    active_ports_pids[port_candidate] = pid
                            except:
                                pass
                except:
                    continue
        
        # Se encontrou múltiplas portas, identifica qual é a ativa (mais recente ou com conexões)
        if len(active_ports_pids) > 1:
            # Verifica qual porta tem conexões ativas (não apenas LISTEN)
            active_port = None
            for port, pid in active_ports_pids.items():
                try:
                    cmd = f"ss -tnp 2>/dev/null | grep ':{port}' | grep -v LISTEN | wc -l"
                    conn_count = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                    if conn_count.isdigit() and int(conn_count) > 0:
                        active_port = port
                        break
                except:
                    pass
            
            # Se não encontrou porta com conexões, usa a primeira (ou 5173 se disponível)
            if not active_port:
                if "5173" in active_ports_pids:
                    active_port = "5173"
                else:
                    active_port = list(active_ports_pids.keys())[0]
            
            # Mata processos nas outras portas (zumbis)
            for port, pid in active_ports_pids.items():
                if port != active_port:
                    try:
                        print(f"[WiFi] Limpando porta zumbi {port} (PID {pid}) após mudança de rede")
                        subprocess.run(f"kill -9 {pid} 2>/dev/null", shell=True, timeout=2)
                    except:
                        pass
        elif len(active_ports_pids) == 1:
            # Apenas uma porta, não precisa limpar nada
            pass
        
    except Exception as e:
        print(f"[WiFi] Aviso ao limpar portas zumbis após mudança de rede: {e}")


def cleanup_zombie_ports(active_port, all_ports):
    """
    ----------------------------------------------------------------------
    @brief Limpa portas zumbis (processos antigos que não são mais o frontend ativo).
    
    @param active_port: Porta do frontend ativo
    @param all_ports: Lista de todas as portas encontradas
    ----------------------------------------------------------------------
    """
    try:
        for port in all_ports:
            if port != active_port:
                try:
                    # Encontra PID usando a porta zumbi
                    cmd = f"ss -tlnp 2>/dev/null | grep ':{port}' | grep LISTEN"
                    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                    if result:
                        import re
                        pid_match = re.search(r'pid=(\d+)', result)
                        if pid_match:
                            pid = int(pid_match.group(1))
                            # Verifica se é processo node/vite
                            try:
                                cmd = f"ps -p {pid} -o comm= 2>/dev/null"
                                proc_name = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE, timeout=1).decode("utf-8").strip()
                                if 'node' in proc_name.lower() or 'vite' in proc_name.lower():
                                    # Mata o processo zumbi
                                    print(f"[WiFi] Limpando porta zumbi {port} (PID {pid})")
                                    subprocess.run(f"kill -9 {pid} 2>/dev/null", shell=True, timeout=2)
                            except:
                                pass
                except:
                    pass
    except Exception as e:
        print(f"[WiFi] Aviso ao limpar portas zumbis: {e}")


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

    # Porta do frontend - detecção inteligente
    frontend_port = detect_frontend_port()
    info["FRONTEND_PORT"] = frontend_port

    return info

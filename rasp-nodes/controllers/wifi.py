import subprocess

def get_connected_ssid():
    try:
        cmd = "nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d: -f2"
        return subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""

def list_available_ssids():
    try:
        subprocess.run(['sudo', 'nmcli', 'dev', 'wifi', 'rescan'], check=True)
        cmd = ['sudo', 'nmcli', '-t', '-f', 'ssid', 'dev', 'wifi', 'list']
        available_ssids = subprocess.check_output(cmd).decode("utf-8").splitlines()

        valid_ssids = []

        for ssid in available_ssids:
            if ssid and ssid not in valid_ssids:
                valid_ssids.append(ssid)

        return valid_ssids
    except subprocess.CalledProcessError:
        return []

def known_connections():
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
    info = {}
    info['HOST'] = subprocess.check_output("hostname", shell=True).decode("utf-8").strip()
    info['IP'] = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True).decode("utf-8").strip()

    try:
        cmd = "iw dev wlan0 link | awk '/signal/ {sig=$2} /tx bitrate/ {rate=$3; printf \"%sdbm|%smbit/s\", sig, rate}'"
        info['WIFI'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        info['WIFI'] = "DESCONECTADO"

    info['SSH'] = subprocess.check_output("systemctl is-active ssh", shell=True).decode("utf-8").strip()
    
    cmd = "who | grep ssh | wc -l"

    info['USERS'] = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    info['SSID'] = get_connected_ssid()
    return info

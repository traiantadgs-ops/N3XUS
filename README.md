# N3XUS v2.2 by TR0JAN

Mobile penetration testing framework for Termux. Written in Python, runs directly from your phone.

**TG GROUP:** `SlientKhanTrollers`

---

## ⚠️ LEGAL DISCLAIMER — READ FIRST

**This tool is for authorized security testing only.**

Using N3XUS against networks, websites, or devices that you do **not** own or do **not** have **explicit written permission** to test is **illegal** in most countries.

**Applicable laws (examples):**
- **Moldova:** Articles on unauthorized access to computer systems
- **United States:** Computer Fraud and Abuse Act (CFAA, 18 U.S.C. § 1030)
- **United Kingdom:** Computer Misuse Act 1990
- **European Union:** Directive 2013/40/EU on attacks against information systems
- **Russia:** Article 272 of the Criminal Code
- **Ukraine:** Article 361 of the Criminal Code

**What this means:**
- Do **not** scan websites you don't own
- Do **not** attack Wi-Fi networks that aren't yours
- Do **not** use DoS module against any target
- Do **not** capture handshakes, PMKID, or credentials from foreign networks
- Do **not** sell access, passwords, or captured data

**Consequences:**
- Criminal charges and prison time
- Fines and confiscation of equipment
- Expulsion from school or university
- Permanent criminal record

**The author (TR0JAN) is not responsible for any misuse of this software.**
You, the user, accept full responsibility for your actions.

---

## 🎯 Features

### [1] 1P L0GG3R
Captures IP address, country, city, and ISP of visitors via Cloudflare Tunnel.
- Deploys Flask server with redirect
- Uses `cloudflared` for public URL
- Saves logs to `~/log.txt`

### [2] S1TE SC4NN3R
Scans a website for vulnerabilities using Nikto, curl, and header analysis.
- Nikto vulnerability scan
- HTTP header analysis
- Page title extraction

### [3] D33R — SUBD0M41N D33P
Deep subdomain enumeration with multiple sources:
- **Subfinder** — fast passive enumeration
- **Amass** — deep passive enumeration
- **crt.sh** — certificate transparency logs (fallback)
- **Live host check** — curl with response codes
- **Separation** — live vs dead hosts
- **Vulnerability scan** — Nikto on discovered hosts

### [4] MASSCAN
Fast port scanning using **masscan** + **nmap -sV**:
- masscan across all 65535 ports (~20x faster than nmap)
- Automatic fallback to `nmap -p-` if masscan fails
- Service version detection via `nmap -sV`
- Connection commands for each open port
- Port descriptions for common services

### [5] SSL CH3CK
SSL/TLS certificate and configuration check:
- Basic check — TLS version, cipher, certificate info
- Deep check — testssl.sh for vulnerabilities (POODLE, DROWN, Heartbleed, etc.)

### [6] D1R3CT0RY BRUT3
Search for hidden files and admin panels:
- 30+ common paths (admin, login, .env, .git, backup, etc.)
- HTTP status codes (200, 401, 403)
- Explanation of what each finding means

### [7] FULL SC4N W3BS1T3S
Complete website security scan:
- **Security headers** — HSTS, CSP, X-Frame-Options, etc.
- **Cookie flags** — Secure, HttpOnly, SameSite
- **CORS misconfiguration** — wildcard origin, reflected origin
- **Open Redirect** — URL parameter manipulation
- **Path Traversal** — /etc/passwd reading attempts
- **Reflected XSS** — HTML/JS context detection
- **SQL Injection** — error-based detection
- **CRLF Injection** — HTTP response splitting
- **robots.txt / sitemap.xml / security.txt**
- **Open ports** — common service scan
- **Hidden files and admin panels**
- **WAF Detection** — Cloudflare, Sucuri, Akamai, etc.
- **CMS Detection** — WordPress, Joomla, Drupal, etc.
- **HTTP Methods** — PUT, DELETE, TRACE
- **Debug endpoints** — phpinfo, actuator, server-status
- **API docs** — swagger, openapi, graphql
- **Email Security** — SPF, DMARC, DKIM
- **Subdomain takeover** — CNAME fingerprinting
- **TLS versions** — SSLv3, TLS 1.0, TLS 1.1
- **Security Headers Score** — A/B/C/D/F grade
- **Open S3/GCS buckets** — AWS, Google Cloud, Azure
- **DNS Zone Transfer** — AXFR attempt
- **CORS null origin** — null-origin bypass
- **Certificate deep** — issuer, SAN, expiry
- **Cookie prefixes** — __Host-, __Secure-
- **Wayback / robots analysis** — archived URLs

### [8] WEB ATTACKS
Web attack module:
- **SQL Injection Scanner** — auto-detection with payloads
- **SQLMap Integration** — full sqlmap run
- **XSS Detection** — reflected XSS payloads
- **LFI/RFI Scanner** — local/remote file inclusion
- **Command Injection** — ping, sleep, whoami payloads
- **SSRF Detection** — internal network access
- **Open Redirect Finder** — URL manipulation
- **CORS Misconfiguration** — wildcard and reflected origins
- **HTTP Header Analysis** — security headers
- **WAF Detection** — Cloudflare, Sucuri, Akamai
- **Full Web Scan** — all of the above

### [9] D0S
Stress test (HTTP Flood + Slowloris):
- **Phone state check** — battery, memory, Wi-Fi
- **Modes** — FULL POWER / SAFE MODE / LOW POWER / BLOCKED
- **Target categories** — Website / Wi-Fi Router / Direct IP
- **Adaptive threads** — automatic adjustment based on error rate
- **Real-time statistics** — requests, errors, RPS, threads
- **Log** — `~/n3xus-dos.log`

**⚠️ Only use against your own infrastructure.**

### [10] NETWORK ATTACKS
Network attack and analysis module:
- **ARP Scan** — network discovery via nmap or scapy
- **Ping Sweep** — ICMP scan of CIDR range
- **TCP Connect Scan** — port scan with banner grabbing
- **SYN Scan** — stealth scan (requires root)
- **Packet Capture** — tcpdump for traffic analysis
- **DNS Sniffing** — port 53 monitoring
- **MAC Address Changer** — spoof MAC address
- **Slowloris** — HTTP stress test
- **Proxy Chain (Tor)** — anonymize traffic
- **Show Network Interfaces** — network info

**⚠️ Only use against your own network.**

---

## 📦 Installation

One command in Termux:

```
bash <(curl -sSL https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/install.sh)
```

# N3XUS v2.1 by TR0JAN

Pentest tool for Termux. Written in Python, runs directly from your phone.

**TG GROUP:** `SlientKhanTrollers`

## Features

- **[1] 1P L0GG3R** — captures IP, country, city and ISP via Cloudflare Tunnel
- **[2] S1TE SC4NN3R** — scans a site for vulnerabilities (Nikto, curl, headers)
- **[3] D33R — SUBD0M41N D33P** — deep subdomain enumeration:
  - Subfinder — fast passive enumeration
  - Amass — deep passive enumeration
  - crt.sh — certificates (fallback)
  - Live host check via curl with response codes
  - Separation into live and dead hosts
  - Vulnerability scan on discovered hosts
- **[4] MASSCAN** — port scanning via **masscan** + **nmap -sV**:
  - masscan across all 65535 ports (~20x faster than nmap)
  - Automatic fallback to `nmap -p-` if masscan fails
  - Service version detection via `nmap -sV`
  - Connection commands for each port
- **[5] SSL CH3CK** — SSL/TLS check (sslscan, testssl.sh)
- **[6] D1R3CT0RY BRUT3** — search for hidden files and admin panels
- **[7] FULL SC4N W3BS1T3S** — full site scan:
  - Security headers (HSTS, CSP, X-Frame-Options)
  - Cookie flags (Secure, HttpOnly, SameSite)
  - CORS misconfig
  - Open Redirect
  - Path Traversal
  - Reflected XSS
  - SQL Injection
  - CRLF Injection
  - robots.txt / sitemap.xml / security.txt
  - Open ports
  - Hidden files and admin panels
  - WAF Detection
  - CMS Detection
  - HTTP Methods (PUT, DELETE, TRACE)
  - Debug endpoints (phpinfo, actuator)
  - API docs (swagger, graphql)
  - Email Security (SPF, DMARC, DKIM)
  - Subdomain takeover
  - TLS versions
  - Security Headers Score
  - Open S3/GCS buckets
  - DNS Zone Transfer (AXFR)
  - CORS null origin
  - Certificate deep
  - Cookie prefixes
  - Wayback / robots analysis
- **[8] WEB ATTACKS** — web attack module:
  - SQL Injection Scanner (Auto)
  - SQLMap Integration
  - XSS Detection (Reflected/Stored)
  - LFI/RFI Scanner
  - Command Injection Tester
  - SSRF Detection
  - Open Redirect Finder
  - CORS Misconfiguration
  - HTTP Header Analysis
  - WAF Detection & Bypass
  - Full Web Scan (All)
- **[9] D0S** — stress test (HTTP Flood + Slowloris):
  - Phone state check (battery, memory, Wi-Fi)
  - Modes: FULL POWER / SAFE MODE / LOW POWER / BLOCKED
  - Target categories: Website / Wi-Fi Router / Direct IP
  - Real-time statistics
  - Log in `~/n3xus-dos.log`

## Installation

One command in Termux:

```
bash <(curl -sSL https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/install.sh)
```

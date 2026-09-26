# N3XUS v2.0 by TR0JAN

Инструмент для пентеста в Termux. Написан на Python, работает прямо с телефона.

**TG:** [@N3XUS_LIKER](https://t.me/N3XUS_LIKER)

## Возможности

- **[1] 1P L0GG3R** — ловит IP, страну, город и провайдера через Cloudflare Tunnel
- **[2] С4ЙТ СК4НН3Р** — сканирует сайт на уязвимости (Nikto, WhatWeb, curl)
- **[3] SUBD0M41N F1ND3R** — поиск поддоменов + проверка на уязвимости
- **[4] P0RT SC4N** — сканирование портов (nmap) + команды подключения
- **[5] SSL CH3CK** — проверка SSL/TLS (sslscan, testssl.sh)
- **[6] D1R3CT0RY BRUT3** — поиск скрытых файлов и админок
- **[7] FULL SC4N W3BS1T3S** — полный скан сайта:
  - Заголовки безопасности (HSTS, CSP, X-Frame-Options)
  - Cookie-флаги (Secure, HttpOnly, SameSite)
  - CORS misconfig
  - Open Redirect
  - Path Traversal
  - Reflected XSS
  - SQL Injection
  - CRLF Injection
  - robots.txt / sitemap.xml / security.txt
  - Открытые порты
  - Скрытые файлы и админки
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

## Установка

Одна команда в Termux:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/install.sh)
```

## Требования

- Android + Termux
- Python 3
- nmap, sslscan, curl, cloudflared, nikto, testssl.sh
- (всё ставится автоматически через install.sh)

## Дисклеймер

Автор не несёт ответственности за использование данного софта.
Используй только на своей инфраструктуре или с разрешения владельца.

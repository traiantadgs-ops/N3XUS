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

**N3XUS** — инструмент для **легального тестирования безопасности** 
и **обучения**. Автор **не несёт ответственности** за любое 
использование данного софта.

### Что разрешено

- Сканирование **своей инфраструктуры** (свои сайты, свои серверы, свои устройства)
- Сканирование **в рамках bug bounty** — только цели **в scope** программы
- Сканирование **с письменного разрешения** владельца системы
- **Обучение** — на специально созданных полигонах (TryHackMe, HackTheBox, DVWA, свои VM)

### Что запрещено

- Сканирование **чужих систем без разрешения** — это **уголовное преступление**
  (Молдова: ст. 259 УК; Россия: ст. 272 УК; и аналогично в других странах)
- Использование **IP Logger** против людей без их согласия — **сбор персональных данных**
- Применение софта для **фишинга**, **шантажа**, **DDoS**, **кражи данных**
- Любое использование, нарушающее **законодательство твоей страны**

### Ответственность

**Ты сам** несёшь ответственность за свои действия. Используя N3XUS, 
ты соглашаешься с тем, что:

- Понимаешь **разницу** между «своё/разрешённое» и «чужое»
- Не будешь применять софт **во вред** другим людям
- Осознаёшь **последствия** (юридические, моральные) своих действий

### Если ты не согласен

**Не используй N3XUS.** Удали его.

---

*N3XUS создан для обучения и защиты, а не для атак.*

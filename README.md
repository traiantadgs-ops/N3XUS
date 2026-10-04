# N3XUS v2.1 by TR0JAN

Инструмент для пентеста в Termux. Написан на Python, работает прямо с телефона.

**TG GROUP:** [SlientKhanTrollers]

## Возможности

- **[1] 1P L0GG3R** — ловит IP, страну, город и провайдера через Cloudflare Tunnel
- **[2] С4ЙТ СК4НН3Р** — сканирует сайт на уязвимости (Nikto, curl, заголовки)
- **[3] D33R — SUBD0M41N D33P** — глубокий поиск поддоменов:
  - Subfinder — быстрый пассивный сбор
  - Amass — глубокий пассивный сбор
  - crt.sh — сертификаты (резерв)
  - Проверка живых через curl с кодом ответа
  - Разделение на живые и мёртвые
  - Сканирование найденных на уязвимости
  - Асинхронный поток — интерфейс не фризит
  - Спиннер и счётчик времени
  - Отмена по `0 + Enter`
- **[4] MASSCAN** — сканирование портов через **masscan** + **nmap -sV**:
  - masscan по всем 65535 портам (быстрее nmap в ~20 раз)
  - Автоматический fallback на `nmap -p-`, если masscan не сработал
  - Определение версий сервисов через `nmap -sV`
  - Команды подключения к каждому порту
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
- **[9] D0S** — нагрузочный тест (HTTP Flood + Slowloris):
  - Проверка состояния телефона (батарея, память, Wi-Fi)
  - Режимы: FULL POWER / SAFE MODE / LOW POWER / BLOCKED
  - Категории целей: Website / Wi-Fi Router / Direct IP
  - Ввод цели вручную
  - Подтверждение `y/n` перед атакой
  - Статистика в реальном времени (запросы, ошибки, RPS)
  - Лог в `~/n3xus-dos.log`
  - Работает ТОЛЬКО на своих целях

## Установка

Одна команда в Termux:

```
bash <(curl -sSL https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/install.sh)
```

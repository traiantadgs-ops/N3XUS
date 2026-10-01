# N3XUS v2.1 by TR0JAN

Инструмент для пентеста в Termux. Написан на Python, работает прямо с телефона.

**TG:** [@N3XUS_LIKER](https://t.me/N3XUS_LIKER)

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

## Установка

Одна команда в Termux:

```
bash <(curl -sSL https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/install.sh)
```

## Требования

- Android + Termux
- Python 3
- Go (для subfinder и amass)
- nmap, sslscan, curl, cloudflared, nikto, testssl.sh, masscan
- (всё ставится автоматически через install.sh)

## Что нового в v2.1

- Модуль `[3]` переработан — теперь использует **subfinder + amass** вместо простого crt.sh
- D33R переведён в **асинхронный поток** — интерфейс не фризит во время сканирования
- Добавлен **спиннер и счётчик времени** в D33R
- Добавлена **отмена** сканирования по `0 + Enter`
- Модуль `[4]` переведён с `nmap -F` на **masscan по всем 65535 портам**
- Автоматический **fallback на nmap -p-**, если masscan не сработал
- Автоматическая установка **Go**, **subfinder**, **amass** в install.sh
- Настройка **PATH** для Go-бинарников
- **Пульсация логотипа** — яркость меняется по циклу

## Дисклеймер

**N3XUS** — инструмент для **легального тестирования безопасности** 
и **обучения**. Автор **не несёт ответственности** за любое 
использование данного софта.

### Что разрешено

- Сканирование **своей инфраструктуры**
- Сканирование **в рамках bug bounty** — только цели **в scope** программы
- Сканирование **с письменного разрешения** владельца системы
- **Обучение** — на полигонах (TryHackMe, HackTheBox, DVWA, свои VM)

### Что запрещено

- Сканирование **чужих систем без разрешения** — уголовное преступление
  (Молдова: ст. 259 УК; Россия: ст. 272 УК)
- Использование **IP Logger** против людей без их согласия
- Применение софта для **фишинга**, **шантажа**, **DDoS**, **кражи данных**
- Любое использование, нарушающее **законодательство твоей страны**

### Ответственность

**Ты сам** несёшь ответственность за свои действия.

### Если ты не согласен

**Не используй N3XUS.** Удали его.

---

*N3XUS создан для обучения и защиты, а не для атак.*

#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  N3XUS v2.1 — установщик"
echo "  TG: @N3XUS_LIKER"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "[!] ДИСКЛЕЙМЕР:"
echo "    Автор не несёт ответственности за использование софта."
echo "    Используй только на своей инфраструктуре или с разрешения."
echo ""
sleep 3

echo "[*] Обновление пакетов..."
pkg update -y && pkg upgrade -y

echo "[*] Установка базовых зависимостей..."
pkg install python git curl nmap sslscan termux-api -y

echo "[*] Установка Go (для subfinder и amass)..."
pkg install golang -y

echo "[*] Установка Flask..."
pip install --break-system-packages flask 2>/dev/null || pkg install python-flask -y

echo "[*] Установка nikto..."
if ! command -v nikto >/dev/null 2>&1; then
    pkg install perl -y
    cd ~
    git clone https://github.com/sullo/nikto.git 2>/dev/null || true
    ln -sf ~/nikto/program/nikto.pl $PREFIX/bin/nikto
    chmod +x ~/nikto/program/nikto.pl
fi

echo "[*] Установка testssl.sh..."
if [ ! -f ~/testssl.sh/testssl.sh ]; then
    cd ~
    git clone https://github.com/drwetter/testssl.sh.git 2>/dev/null || true
    chmod +x ~/testssl.sh/testssl.sh
fi

echo "[*] Установка cloudflared..."
pkg install cloudflared -y 2>/dev/null || true

echo "[*] Установка subfinder..."
if ! command -v subfinder >/dev/null 2>&1; then
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
fi

echo "[*] Установка amass..."
if ! command -v amass >/dev/null 2>&1; then
    go install -v github.com/owasp-amass/amass/v4/...@latest
fi

echo "[*] Настройка PATH для Go-бинарников..."
if ! grep -q 'go/bin' ~/.bashrc 2>/dev/null; then
    echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
fi
export PATH=$PATH:$HOME/go/bin

echo "[*] Скачивание N3XUS.py..."
cd ~
curl -fsSL -o N3XUS.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/N3XUS.py

echo ""
echo "[+] Установка завершена!"
echo "[+] Проверка инструментов:"
echo "    subfinder: $(command -v subfinder || echo 'нет')"
echo "    amass:     $(command -v amass || echo 'нет')"
echo ""
echo "[+] Запуск N3XUS..."
echo ""
sleep 2

python ~/N3XUS.py

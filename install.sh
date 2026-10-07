#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  N3XUS v2.2 — installer"
echo "  TG GROUP: SlientKhanTrollers"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "[!] DISCLAIMER:"
echo "    The author is not responsible for the use of this software."
echo "    Use it only on your own infrastructure or with permission."
echo ""
sleep 3

echo "[*] Updating packages..."
pkg update -y && pkg upgrade -y

echo "[*] Installing base dependencies..."
pkg install python git curl nmap sslscan termux-api clang make -y

echo "[*] Installing Go (for subfinder and amass)..."
pkg install golang -y

echo "[*] Installing Flask..."
pip install --break-system-packages flask 2>/dev/null || pkg install python-flask -y

echo "[*] Installing nikto..."
if ! command -v nikto >/dev/null 2>&1; then
    pkg install perl -y
    cd ~
    git clone https://github.com/sullo/nikto.git 2>/dev/null || true
    ln -sf ~/nikto/program/nikto.pl $PREFIX/bin/nikto
    chmod +x ~/nikto/program/nikto.pl
fi

echo "[*] Installing testssl.sh..."
if [ ! -f ~/testssl.sh/testssl.sh ]; then
    cd ~
    git clone https://github.com/drwetter/testssl.sh.git 2>/dev/null || true
    chmod +x ~/testssl.sh/testssl.sh
fi

echo "[*] Installing cloudflared..."
pkg install cloudflared -y 2>/dev/null || true

echo "[*] Installing masscan (building from source)..."
if ! command -v masscan >/dev/null 2>&1; then
    cd ~
    if [ ! -d ~/masscan ]; then
        git clone https://github.com/robertdavidgraham/masscan.git 2>/dev/null || true
    fi
    if [ -d ~/masscan ]; then
        cd ~/masscan
        make 2>/dev/null || true
        if [ -f ~/masscan/bin/masscan ]; then
            cp ~/masscan/bin/masscan $PREFIX/bin/masscan
            chmod +x $PREFIX/bin/masscan
        fi
    fi
fi

echo "[*] Installing subfinder..."
if ! command -v subfinder >/dev/null 2>&1; then
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
fi

echo "[*] Installing amass..."
if ! command -v amass >/dev/null 2>&1; then
    go install -v github.com/owasp-amass/amass/v4/...@latest
fi

echo "[*] Setting up PATH for Go binaries..."
if ! grep -q 'go/bin' ~/.bashrc 2>/dev/null; then
    echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
fi
export PATH=$PATH:$HOME/go/bin

echo "[*] Downloading N3XUS.py..."
cd ~
curl -fsSL -o N3XUS.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/N3XUS.py

echo "[*] Downloading web_attacks.py..."
curl -fsSL -o web_attacks.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/web_attacks.py

echo "[*] Downloading network_attack_n3xus.py..."
curl -fsSL -o network_attack_n3xus.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/network_attack_n3xus.py

echo "[*] Downloading n3xus-dos.py..."
curl -fsSL -o n3xus-dos.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/n3xus-dos.py

echo ""
echo "[+] Installation complete!"
echo "[+] Tool check:"
echo "    subfinder: $(command -v subfinder || echo 'not found')"
echo "    amass:     $(command -v amass || echo 'not found')"
echo "    masscan:   $(command -v masscan || echo 'not found')"
echo "    nikto:     $(command -v nikto || echo 'not found')"
echo "    nmap:      $(command -v nmap || echo 'not found')"
echo "    sslscan:   $(command -v sslscan || echo 'not found')"
echo ""
echo "[+] Starting N3XUS..."
echo ""
sleep 2

python ~/N3XUS.py

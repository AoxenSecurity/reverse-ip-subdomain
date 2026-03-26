from __future__ import print_function
import os
import sys
import subprocess

REQUIRED_PACKAGES = {
    "requests": "requests",
    "colorama": "colorama",
}

if sys.version_info[0] < 3:
    REQUIRED_PACKAGES["concurrent.futures"] = "futures"

def install_missing():
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print("[*] Installing missing packages: {0}".format(", ".join(missing)))
        devnull = open(os.devnull, "w")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing,
                stdout=devnull,
                stderr=subprocess.STDOUT,
            )
        finally:
            devnull.close()
        print("[+] Packages installed successfully!\n")

install_missing()

import time
import threading
import io
import webbrowser
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

if sys.version_info[0] < 3:
    input = raw_input

R = Fore.RED
G = Fore.GREEN
Y = Fore.YELLOW
C = Fore.CYAN
M = Fore.MAGENTA
W = Fore.WHITE
B = Fore.BLUE
RST = Style.RESET_ALL
DIM = Style.DIM
BRIGHT = Style.BRIGHT

API_BASE = "https://api.dnsrift.net"
THREADS = 30
lock = threading.Lock()
stats = {"total_found": 0, "total_targets": 0, "processed": 0, "errors": 0}


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    clear()
    art = [
        " ____  _   _ ____  ____  ___ _____ _____ ",
        "|  _ \\| \\ | / ___||  _ \\|_ _|  ___|_   _|",
        "| | | |  \\| \\___ \\| |_) || || |_    | |  ",
        "| |_| | |\\  |___) |  _ < | ||  _|   | |  ",
        "|____/|_| \\_|____/|_| \\_\\___|_|     |_|  ",
    ]
    tag_a = "Reverse IPs & Subdomain  "
    tag_b = "// powered by dnsrift.net"
    tag_full = tag_a + tag_b
    w = max(max(len(l) for l in art), len(tag_full))
    border = "+" + "-" * (w + 4) + "+"
    empty = "|" + " " * (w + 4) + "|"

    print("")
    print("{C}{BR}{v}{RST}".format(C=C, BR=BRIGHT, RST=RST, v=border))
    print("{C}{BR}{v}{RST}".format(C=C, BR=BRIGHT, RST=RST, v=empty))
    for l in art:
        pad = w - len(l)
        left = pad // 2
        right = pad - left
        row = "|  " + " " * left + l + " " * right + "  |"
        print("{C}{BR}{v}{RST}".format(C=C, BR=BRIGHT, RST=RST, v=row))
    print("{C}{BR}{v}{RST}".format(C=C, BR=BRIGHT, RST=RST, v=empty))
    tpad = w - len(tag_full)
    tleft = tpad // 2
    tright = tpad - tleft
    print("{C}{BR}|  {sp1}{W}{a}{DIM}{b}{RST}{C}{BR}{sp2}  |{RST}".format(
        C=C, BR=BRIGHT, W=W, DIM=DIM, RST=RST,
        a=tag_a, b=tag_b, sp1=" " * tleft, sp2=" " * tright))
    print("{C}{BR}{v}{RST}".format(C=C, BR=BRIGHT, RST=RST, v=empty))
    print("{C}{BR}{v}{RST}".format(C=C, BR=BRIGHT, RST=RST, v=border))
    print("")


def print_info(msg):
    print("  {C}[{W}INFO{C}]{RST} {msg}".format(C=C, W=W, RST=RST, msg=msg))


def print_success(msg):
    print("  {G}[{W} +  {G}]{RST} {msg}".format(G=G, W=W, RST=RST, msg=msg))


def print_warn(msg):
    print("  {Y}[{W}WARN{Y}]{RST} {msg}".format(Y=Y, W=W, RST=RST, msg=msg))


def print_error(msg):
    print("  {R}[{W}FAIL{R}]{RST} {msg}".format(R=R, W=W, RST=RST, msg=msg))


def print_result(label, value):
    print("  {M}  |--{RST} {DIM}{label}:{RST} {G}{value}{RST}".format(
        M=M, RST=RST, DIM=DIM, G=G, label=label, value=value))


def separator():
    print("\n  {C}{DIM}{line}{RST}\n".format(C=C, DIM=DIM, RST=RST, line="-" * 60))


def validate_api_key(key):
    try:
        resp = requests.get(
            API_BASE + "/reverse-ip-lookup",
            params={"ip": "8.8.8.8", "key": key},
            timeout=15,
        )
        data = resp.json()
        plan = data.get("plan", "free")
        if plan != "free":
            return True
        if "message" in data and "invalid" in data["message"].lower():
            return False
        return True
    except Exception:
        return False


def get_api_key():
    separator()
    print_info("API Key Configuration")
    print("  {DIM}  Free plan: no key needed (100K results/day)".format(DIM=DIM))
    print("  {DIM}  Paid plans: higher limits & more results{RST}".format(DIM=DIM, RST=RST))
    print("")
    key = input("  {C}[{W}?{C}]{RST} Enter API key {DIM}(press Enter to skip):{RST} ".format(
        C=C, W=W, RST=RST, DIM=DIM)).strip()

    if not key:
        print_warn("No API key provided -- using free plan")
        return ""

    print_info("Validating API key...")
    if validate_api_key(key):
        print_success("API key is valid!")
        return key
    else:
        print_error("API key validation failed -- falling back to free plan")
        return ""


def reverse_ip_lookup(ip, api_key, output_file):
    ip = ip.strip()
    params = {"ip": ip}
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(
            API_BASE + "/reverse-ip-lookup",
            params=params,
            timeout=30,
        )
        data = resp.json()

        if resp.status_code != 200 or "message" in data:
            with lock:
                stats["errors"] += 1
                print_error("{ip} -- {msg}".format(ip=ip, msg=data.get("message", "Unknown error")))
            return

        domains = data.get("domain_list", [])
        count = data.get("domain_count", len(domains))

        with lock:
            stats["processed"] += 1
            stats["total_found"] += count

            if domains:
                print_success("{C}{ip}{RST} -> {G}{count}{RST} domain(s) found".format(
                    C=C, G=G, RST=RST, ip=ip, count=count))
                for d in domains:
                    print_result("domain", d)
                with io.open(output_file, "a", encoding="utf-8") as f:
                    for d in domains:
                        f.write(d + "\n")
            else:
                print_warn("{ip} -> 0 domains".format(ip=ip))

    except requests.exceptions.Timeout:
        with lock:
            stats["errors"] += 1
            print_error("{ip} -- Request timed out".format(ip=ip))
    except Exception as e:
        with lock:
            stats["errors"] += 1
            print_error("{ip} -- {err}".format(ip=ip, err=str(e)[:80]))


def subdomain_lookup(domain, api_key, output_file):
    domain = domain.strip()
    params = {"domain": domain}
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(
            API_BASE + "/subdomain-lookup",
            params=params,
            timeout=30,
        )
        data = resp.json()

        if resp.status_code != 200 or "message" in data:
            with lock:
                stats["errors"] += 1
                print_error("{d} -- {msg}".format(d=domain, msg=data.get("message", "Unknown error")))
            return

        subs = data.get("subdomains", [])
        count = data.get("count", len(subs))

        with lock:
            stats["processed"] += 1
            stats["total_found"] += count

            if subs:
                print_success("{C}{d}{RST} -> {G}{count}{RST} subdomain(s) found".format(
                    C=C, G=G, RST=RST, d=domain, count=count))
                for s in subs:
                    print_result("sub", s)
                with io.open(output_file, "a", encoding="utf-8") as f:
                    for s in subs:
                        f.write(s + "\n")
            else:
                print_warn("{d} -> 0 subdomains".format(d=domain))

    except requests.exceptions.Timeout:
        with lock:
            stats["errors"] += 1
            print_error("{d} -- Request timed out".format(d=domain))
    except Exception as e:
        with lock:
            stats["errors"] += 1
            print_error("{d} -- {err}".format(d=domain, err=str(e)[:80]))


def load_targets():
    separator()
    print_info("Target Input")
    print("  {DIM}  Load targets from a .txt file (one per line){RST}".format(DIM=DIM, RST=RST))
    print("")

    path = input("  {C}[{W}?{C}]{RST} File path: ".format(C=C, W=W, RST=RST)).strip().strip('"').strip("'")
    if not os.path.isfile(path):
        print_error("File not found!")
        sys.exit(1)
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        targets = [line.strip() for line in f if line.strip()]
    if not targets:
        print_error("File is empty!")
        sys.exit(1)
    print_success("Loaded {G}{n}{RST} targets from file".format(G=G, RST=RST, n=len(targets)))
    return targets


def choose_mode():
    separator()
    print("  {C}{BR}  Select Operation Mode{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("")
    print("  {G}  [{W}1{G}]{RST} {BR}Reverse IP Lookup{RST}    {DIM}-- IP -> Domains{RST}".format(
        G=G, W=W, RST=RST, BR=BRIGHT, DIM=DIM))
    print("  {G}  [{W}2{G}]{RST} {BR}Subdomain Lookup{RST}     {DIM}-- Domain -> Subdomains{RST}".format(
        G=G, W=W, RST=RST, BR=BRIGHT, DIM=DIM))
    print("  {Y}  [{W}3{Y}]{RST} {BR}Buy API Key{RST}          {DIM}-- Faster speeds & more results{RST}".format(
        Y=Y, W=W, RST=RST, BR=BRIGHT, DIM=DIM))
    print("")
    choice = input("  {C}[{W}?{C}]{RST} Choose {G}[1/2/3]{RST}: ".format(
        C=C, W=W, RST=RST, G=G)).strip()

    if choice in ("1", "2"):
        return int(choice)
    if choice == "3":
        separator()
        print_info("Opening {C}https://dnsrift.net/pricing{RST} ...".format(C=C, RST=RST))
        print("")
        print("  {Y}{BR}  Plans available:{RST}".format(Y=Y, BR=BRIGHT, RST=RST))
        print("  {W}  Free          {G}$0{W}        {DIM}100K req/day   -- no key needed{RST}".format(
            W=W, G=G, DIM=DIM, RST=RST))
        print("  {W}  Professional  {G}$50{W}/mo   {DIM}1M req/month   -- 500K results/req{RST}".format(
            W=W, G=G, DIM=DIM, RST=RST))
        print("  {W}  Enterprise    {G}$100{W}/mo  {DIM}3M req/month   -- unlimited results{RST}".format(
            W=W, G=G, DIM=DIM, RST=RST))
        print("")
        print("  {DIM}  Payment: USDT (TRC20), USDT (Solana), Bitcoin{RST}".format(DIM=DIM, RST=RST))
        webbrowser.open("https://dnsrift.net/pricing")
        separator()
        print_info("After purchasing, restart the tool and enter your API key.")
        sys.exit(0)
    print_error("Invalid choice!")
    sys.exit(1)


def print_summary(output_file, elapsed):
    separator()
    print("  {C}{BR}  +===================================+{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("  {C}{BR}  |        SCAN COMPLETE              |{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("  {C}{BR}  +===================================+{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("")
    print("  {W}  Targets processed : {G}{v}{RST}".format(W=W, G=G, RST=RST, v=stats["processed"]))
    print("  {W}  Total found       : {G}{v}{RST}".format(W=W, G=G, RST=RST, v=stats["total_found"]))
    print("  {W}  Errors            : {R}{v}{RST}".format(W=W, R=R, RST=RST, v=stats["errors"]))
    print("  {W}  Time elapsed      : {Y}{v:.2f}s{RST}".format(W=W, Y=Y, RST=RST, v=elapsed))
    print("  {W}  Threads used      : {M}{v}{RST}".format(W=W, M=M, RST=RST, v=THREADS))
    print("  {W}  Results saved to  : {C}{v}{RST}".format(W=W, C=C, RST=RST, v=output_file))
    separator()


def main():
    banner()

    api_key = get_api_key()
    mode = choose_mode()
    targets = load_targets()

    stats["total_targets"] = len(targets)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if mode == 1:
        output_file = "reverse_ip_results_{0}.txt".format(timestamp)
        mode_label = "Reverse IP Lookup"
        worker = reverse_ip_lookup
    else:
        output_file = "subdomain_results_{0}.txt".format(timestamp)
        mode_label = "Subdomain Lookup"
        worker = subdomain_lookup

    if not os.path.isdir("results"):
        os.makedirs("results")
    output_file = os.path.join("results", output_file)

    separator()
    print("  {C}{BR}  +===================================+{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("  {C}{BR}  |        STARTING SCAN              |{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("  {C}{BR}  +===================================+{RST}".format(C=C, BR=BRIGHT, RST=RST))
    print("")
    print("  {W}  Mode      : {G}{v}{RST}".format(W=W, G=G, RST=RST, v=mode_label))
    print("  {W}  Targets   : {G}{v}{RST}".format(W=W, G=G, RST=RST, v=len(targets)))
    print("  {W}  Threads   : {M}{v}{RST}".format(W=W, M=M, RST=RST, v=THREADS))
    print("  {W}  API Key   : {clr}{v}{RST}".format(
        W=W, RST=RST, clr=G if api_key else Y, v="Configured" if api_key else "Free Plan"))
    print("  {W}  Output    : {C}{v}{RST}".format(W=W, C=C, RST=RST, v=output_file))
    separator()

    start = time.time()

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        futures = []
        for target in targets:
            futures.append(pool.submit(worker, target, api_key, output_file))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                with lock:
                    stats["errors"] += 1
                    print_error("Thread exception: {0}".format(str(e)[:80]))

    elapsed = time.time() - start
    print_summary(output_file, elapsed)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  {R}[!] Interrupted by user{RST}\n".format(R=R, RST=RST))
        sys.exit(0)

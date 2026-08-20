"""Debug NSE access through multiple approaches."""
import json
import requests

BASE = "https://www.nseindia.com"

def dump(name, resp):
    print(f"--- {name} --- status={resp.status_code}")
    print(resp.headers.get("content-type"), resp.headers.get("set-cookie", "")[:120])
    print(resp.text[:150].replace("\n", " "))
    print()

H = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "accept": "*/*",
    "accept-language": "en-GB,en;q=0.9",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": BASE + "/option-chain",
}

# Approach 1: page then API in same session
s = requests.Session()
s.headers.update(H)
s.get("https://www.google.com", timeout=10)  # warm session
r = s.get(f"{BASE}/", headers=H, timeout=15)
dump("homepage", r)
r = s.get(f"{BASE}/api/equity-stockIndices?index=NIFTY 500", headers=H, timeout=15)
dump("stockIndices after homepage", r)

# Approach 2: option-chain page first
s2 = requests.Session()
s2.headers.update(H)
r = s2.get(f"{BASE}/option-chain", headers=H, timeout=15)
dump("option-chain page", r)
r = s2.get(f"{BASE}/api/equity-stockIndices?index=NIFTY 500", headers=H, timeout=15)
dump("stockIndices after option-chain", r)

# Approach 3: curl from shell comparison
import subprocess
out = subprocess.run(
    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
     "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500",
     "-H", "user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"],
    capture_output=True, text=True, timeout=30)
print("curl stockIndices:", out.stdout)

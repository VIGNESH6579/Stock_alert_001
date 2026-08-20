"""Third round: NSE bhavcopy archives, StocksRin real API, ticker variants."""
import json
import requests

H = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

# 1. NSE bhavcopy archives (official public endpoint)
urls = [
    "https://archives.nseindia.com/content/historical/EQUITIES/2026/AUG/cm18AUG2026bhav.csv.zip",
    "https://www.nseindia.com/content/historical/EQUITIES/2026/AUG/cm18AUG2026bhav.csv.zip",
]
for u in urls:
    try:
        r = requests.get(u, headers=H, timeout=30, stream=True)
        print("bhavcopy", u.split('/')[-1], "status", r.status_code,
              "ct", r.headers.get("content-type", ""), "len", r.headers.get("content-length"))
        if r.status_code == 200:
            open("/tmp/bhav.zip", "wb").write(r.content[:2000])
    except Exception as exc:
        print("bhavcopy ERR", exc)

# 2. StocksRin - look at homepage source for data endpoints
import re
try:
    home = open("/tmp/stocksrin_home.html", encoding="utf-8", errors="ignore").read()
    apis = sorted(set(re.findall(r'"(/api/[^"\'? ]*)"', home)) +
                  set(re.findall(r'(fetch\(["\'])([^"\']+)', home)))
    print("stocksrin api paths found:", list(apis)[:30])
except Exception as exc:
    print("parse err", exc)

# 3. TATAMOTORS ticker variants on yfinance
import yfinance as yf
for tick in ["TATAMOTORS.NS"]:
    t = yf.Ticker(tick)
    try:
        h = t.history(period="2d", interval="5m")
        print(tick, "rows", len(h))
        if len(h):
            print(h.tail(1))
    except Exception as exc:
        print(tick, "ERR", str(exc)[:100])

# quick NSE symbol check via Yahoo crumb-free quote API
try:
    r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/TATAMOTORS.NS",
                     params={"interval": "5m", "range": "2d"}, headers=H, timeout=20)
    d = r.json()
    res = d.get("chart", {}).get("result")
    print("yahoo chart API:", r.status_code,
          "ts_count", len(res[0]["timestamp"]) if res else "null")
except Exception as exc:
    print("yahoo chart ERR", str(exc)[:100])

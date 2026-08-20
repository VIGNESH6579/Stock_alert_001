"""Probe alternative free sources for NSE option-chain data."""
import json
import requests

H = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept": "*/*",
}


def try_get(name, url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=15, **kw)
        print(f"{name}: {r.status_code} len={len(r.text)}")
        print(r.text[:200].replace("\n", " "))
        print()
        return r
    except Exception as exc:
        print(f"{name}: ERROR {exc}\n")
        return None


# StocksRin public option chain endpoint
try_get("stocksrin TATAMOTORS",
        "https://stocksrin.com/api/optionchain/TATAMOTORS")
try_get("stocksrin option chain json",
        "https://stocksrin.com/api/optionchain-json/TATAMOTORS")

# Unofficed nse-python public mirror endpoints
for url in [
    "https://unofficed.com/api/nse/getoptionchain/?symbol=TATAMOTORS",
    "https://unofficed.com/api/nse/",
]:
    try_get("unofficed: " + url, url)

# Dhan API (requires token, but test root)
try_get("dhan api", "https://api.dhan.co/v2/")

# yfinance as price fallback check
import yfinance as yf
t = yf.Ticker("TATAMOTORS.NS")
h = t.history(period="5d", interval="5m")
print("yfinance TATAMOTORS.NS 5m bars:", len(h))
print(h.tail(2))

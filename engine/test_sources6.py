"""Probe StocksRin with a full session (it may need cookies), and Stooq CSV download."""
import re
import requests

H = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

# StocksRin session-based fetch
s = requests.Session()
s.headers.update(H)
r = s.get("https://stocksrin.com/", timeout=20)
print("stocksrin home cookies:", dict(r.cookies))
r = s.get("https://stocksrin.com/api/optionchain/TATAMOTORS", timeout=20)
print("optionchain after session:", r.status_code, len(r.text), r.text[:100].replace("\n", " "))

# StocksRin: check their actual network calls via common pattern
for p in [
    "https://stocksrin.com/api/market/option-chain?symbol=TATAMOTORS",
    "https://stocksrin.com/optionchain/TATAMOTORS",
    "https://stocksrin.com/api/v1/option_chain?symbol=TATAMOTORS",
]:
    r2 = s.get(p, timeout=20)
    print(p.split("stocksrin.com")[-1], r2.status_code, len(r2.text), r2.text[:60].replace("\n", " "))

# Stooq intraday CSV for RELIANCE
r = s.get("https://stooq.com/q/d/l/", params={"s": "reliance.pl", "i": "d"}, timeout=20)
print("stooq daily:", r.status_code, len(r.text), r.text[:150])

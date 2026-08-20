"""Probe remaining free sources: sensibull, Dhan option chain, StockAnalysisIN, Google-free mirrors."""
import requests

H = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
     "accept": "application/json, */*"}

def probe(name, url, params=None):
    try:
        r = requests.get(url, headers=H, params=params or {}, timeout=15)
        head = r.text[:130].replace("\n", " ")
        print(f"{name} [{r.status_code}] {head}")
        if r.status_code == 200 and len(r.text) > 1000:
            open(f"/tmp/probe_{name.replace('/', '_')}.txt", "w").write(r.text)
        return r
    except Exception as exc:
        print(f"{name}: ERR {str(exc)[:90]}")

# sensibull public endpoints
probe("sensibull chain", "https://sensibull.com/api/v1/option_chain",
      params={"symbol": "TATAMOTORS"})
probe("sensibull options", "https://sensibull.com/trading/option-chain")

# Dhan v2 public-ish option chain (public token? try)
probe("dhan chain", "https://api.dhan.co/v2/option-chain?symbol=TATAMOTORS")

# upstox public mirror used by many free tools
probe("upstox", "https://api.upstox.com/v2/option-chain?symbol=TATAMOTORS")

# stooq for Indian stock prices
probe("stooq", "https://stooq.com/q/d/l/?s=tatamotors.pl&i=d",
      params={"s": "tatamotors.pl", "i": "d"})

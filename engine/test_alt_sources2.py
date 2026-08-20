"""Second round of source probing with corrected parameters."""
import json
import requests

H = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept": "application/json, text/javascript, */*",
}

def try_get(name, url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=20, **kw)
        txt = r.text[:150].replace("\n", " ")
        print(f"{name}: {r.status_code} len={len(r.text)} | {txt}")
        return r
    except Exception as exc:
        print(f"{name}: ERROR {exc}")
        return None

# StocksRin — search their API surface
for p in [
    "https://stocksrin.com/api/option_chain/stocks?symbol=TATAMOTORS",
    "https://stocksrin.com/api/options/data",
    "https://stocksrin.com/api/nse_data/optionchain?symbol=TATAMOTORS",
]:
    try_get("stocksrin alt", p)

# StocksRin main page to find API docs
r = try_get("stocksrin root", "https://stocksrin.com/")
if r and r.status_code == 200:
    with open("/tmp/stocksrin_home.html", "w") as f:
        f.write(r.text)

# yfinance with correct ticker format
import yfinance as yf
for tick in ["TATAMOTORS.NS", "TATASTEEL.NS"]:
    try:
        t = yf.Ticker(tick)
        h = t.history(period="2d", interval="5m")
        print(f"yfinance {tick}: rows={len(h)} last={h['Close'].iloc[-1] if len(h) else None}")
    except Exception as exc:
        print(f"yfinance {tick}: ERROR {exc}")

# test downloading NSE bhavcopy zip (public archives)
try:
    r = requests.get(
        "https://npgwebsite.ntpc.co.in/equities/EQ180826.csv.zip", timeout=20, headers=H)
    print("bhavcopy attempt:", r.status_code)
except Exception as exc:
    print("bhavcopy:", exc)

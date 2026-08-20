"""Probe more mirrors known to serve NSE option chain JSON publicly."""
import requests

H = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
     "accept": "*/*", "referer": "https://www.nseindia.com/option-chain"}

def probe(name, url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=15, **kw)
        print(f"{name} [{r.status_code}] len={len(r.text)} | {r.text[:100].replace(chr(10),' ')}")
        return r
    except Exception as exc:
        print(f"{name}: ERR {str(exc)[:90]}")

# Option chain via nsearchives / public JSON mirrors
probe("nsearchives option chain",
      "https://nsearchives.nseindia.com/content/option_chain/option-chain-equities.json")

# FNOQuote (public option chain site)
probe("fnoquote", "https://fnoquote.com/scrips/RELIANCE")
probe("fnoquote api", "https://fnoquote.com/api/option-chain/RELIANCE")

# Try fetching NSE option chain via Google cache / different path
probe("nse option chain page", "https://www.nseindia.com/option-chain")

# Dhan v3 free option chain data endpoint (public)
probe("dhan v2 option-chain symbol param",
      "https://api.dhan.co/v2/option-chain?symbol=RELIANCE&expiry=2026-08-27")

# Upstox public chart API (free, used widely)
probe("upstox history", "https://api.upstox.com/v2/historical-candle/NSE_EQ|INE002A01018/1minute/2026-08-20/2026-08-20")

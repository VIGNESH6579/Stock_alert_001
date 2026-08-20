"""Validate universe tickers via yfinance (TradingView/Yahoo feed)."""
import json
import yfinance as yf
import pandas as pd

syms = json.load(open("/home/ubuntu/option_scalp/data/universe.json"))
bad = []
ok_count = 0
for s in syms:
    if not s.replace("&", "").replace("-", "").isalnum():
        bad.append((s, "invalid chars"))
        continue
    try:
        t = yf.Ticker(s + ".NS")
        h = t.history(period="10d")
        if len(h) < 3:
            bad.append((s, f"only {len(h)} daily rows"))
        else:
            ok_count += 1
    except Exception as exc:
        bad.append((s, str(exc)[:60]))
print("valid:", ok_count, "| suspect:", len(bad))
for s, r in bad:
    print("  ?", s, "->", r)

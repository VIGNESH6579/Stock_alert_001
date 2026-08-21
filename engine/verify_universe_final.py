"""Validate every symbol in universe_final.json against the yfinance feed."""
import json
import random
import time

import yfinance as yf

d = json.load(open("data/universe_final.json"))
symbols = d["symbols"]
ok, bad = [], []
for i, sym in enumerate(symbols):
    try:
        df = yf.Ticker(sym + ".NS").history(period="5d", interval="5m",
                                             auto_adjust=False)
        if df is not None and len(df) >= 10:
            ok.append(sym)
        else:
            bad.append((sym, "empty"))
    except Exception as e:
        bad.append((sym, str(e)[:40]))
    if (i + 1) % 25 == 0:
        print(f"{i+1}/{len(symbols)} done, bad so far: {len(bad)}", flush=True)
    time.sleep(random.uniform(0.15, 0.4))

print("\nVALID:", len(ok), "| BAD:", len(bad))
for b in bad:
    print("  BAD:", b)
json.dump({"valid": ok, "invalid": bad}, open("data/universe_final_valid.json",
                                              "w"), indent=1)

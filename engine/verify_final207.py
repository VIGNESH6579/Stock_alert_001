"""Final verification of the 207-symbol universe."""
import json
import time
import yfinance as yf

d = json.load(open("data/universe_final.json"))
symbols = d["symbols"]
bad = []
for i, sym in enumerate(symbols):
    ok = False
    for a in range(3):
        try:
            df = yf.Ticker(sym + ".NS").history(period="5d", interval="5m", auto_adjust=False)
            if df is not None and len(df) >= 5:
                ok = True
                break
        except Exception:
            pass
        time.sleep(3)
    if not ok:
        bad.append(sym)
    if (i + 1) % 50 == 0:
        print(i + 1, "done, bad:", len(bad), flush=True)
print("VALID:", len(symbols) - len(bad), "| BAD:", bad)
json.dump(bad, open("data/final207_bad.json", "w"), indent=1)

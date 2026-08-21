"""Re-check the 8 failing symbols with retries and longer waits."""
import json
import time

import yfinance as yf

bad = [s for s, _ in json.load(open("data/universe_final_valid.json"))["invalid"]]
print("rechecking:", bad)
ok = []
for sym in bad:
    got = None
    for attempt in range(4):
        try:
            df = yf.Ticker(sym + ".NS").history(period="1mo", interval="5m",
                                                 auto_adjust=False)
            if df is not None and len(df) >= 5:
                got = len(df)
                break
        except Exception as e:
            print(f"  {sym} attempt {attempt}: {str(e)[:60]}")
        time.sleep(6)
    if got:
        ok.append(sym)
        print(f"  {sym}: OK ({got} rows)")
    else:
        print(f"  {sym}: STILL BAD")
print("\nrecovered:", ok)

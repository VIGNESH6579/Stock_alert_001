import time
import yfinance as yf

for sym in ["MCDOWELL-N", "NALCO", "NIPPOINDIA", "ZOMATO"]:
    ok = False
    for a in range(3):
        try:
            df = yf.Ticker(sym + ".NS").history(period="5d", interval="5m", auto_adjust=False)
            if df is not None and len(df) >= 5:
                print(sym, "OK", len(df)); ok = True; break
        except Exception as e:
            print(sym, "ERR", str(e)[:60])
        time.sleep(10)
    if not ok:
        print(sym, "STILL BAD")
    time.sleep(5)

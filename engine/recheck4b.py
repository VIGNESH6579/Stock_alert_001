import time
import yfinance as yf

tests = {
    "UNITDSPR": "United Spirits",
    "NATIONALUM": "NALCO",
    "ETERNAL": "Zomato",
    "NIAMC": "Nippon India AMC (NIAMC)",
}
for sym, name in tests.items():
    ok = False
    for a in range(3):
        try:
            df = yf.Ticker(sym + ".NS").history(period="5d", interval="5m", auto_adjust=False)
            if df is not None and len(df) >= 5:
                print(sym, name, "OK", len(df)); ok = True; break
        except Exception as e:
            print(sym, name, "ERR", str(e)[:60])
        time.sleep(5)
    if not ok:
        print(sym, name, "STILL BAD")
    time.sleep(3)

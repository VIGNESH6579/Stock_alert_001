import time
import yfinance as yf

tests = {
    "LTIM (old)": "LTIM",
    "LTIMINDTREE": "LTIMINDTREE",
    "MCDOWELL-N": "MCDOWELL-N",
    "MCDOWELL-N.NS alt": "MCDOWELL.NS",
    "NALCO": "NALCO",
    "NIPPOINDIA": "NIPPOINDIA",
    "ZOMATO": "ZOMATO",
}
for name, sym in tests.items():
    ok = False
    for attempt in range(3):
        try:
            df = yf.Ticker(sym + ".NS").history(period="5d", interval="5m", auto_adjust=False)
            if df is not None and len(df) >= 5:
                print(f"{name}: OK ({len(df)})"); ok = True; break
        except Exception as e:
            print(f"{name}: ERR {str(e)[:50]}")
        time.sleep(5)
    if not ok:
        print(f"{name}: STILL BAD")
    time.sleep(2)

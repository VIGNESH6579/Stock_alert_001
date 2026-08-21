"""Test corrected tickers for the 8 failing symbols."""
import time

import yfinance as yf

candidates = {
    "GE Vernova": "GVT&D",
    "GMRINFRA": "GMRAIRPORT",
    "HITACHI": "HIRECT",
    "LTIM": "LTIM",
    "MCDOWELL-N": "MCDOWELL-N",
    "NALCO": "NALCO",
    "NIPPOINDIA": "NIPPOINDIA",
    "ZOMATO": "ZOMATO",
}
for name, sym in candidates.items():
    ok = False
    for attempt in range(3):
        try:
            df = yf.Ticker(sym + ".NS").history(period="5d", interval="5m",
                                                 auto_adjust=False)
            if df is not None and len(df) >= 5:
                print(f"{name} -> {sym}: OK ({len(df)} rows)")
                ok = True
                break
        except Exception as e:
            print(f"{name} -> {sym}: ERR {str(e)[:50]}")
        time.sleep(4)
    if not ok:
        print(f"{name} -> {sym}: STILL BAD")
    time.sleep(2)

"""Check suspect tickers with alternatives."""
import yfinance as yf

candidates = {
    "HITACHI": ["HITACHI.NS"],
    "MCDOWELL-N": ["UNITDSPR.NS"],
    "NIPPOINDIA": ["NIPPOINDIAMF.NS"],
    "TATAMOTORS": ["TATAMOTORS.NS"],
    "ZOMATO": ["ZOMATO.NS"],
}
import time
for orig, tries in candidates.items():
    for t in tries:
        try:
            h = yf.Ticker(t).history(period="10d")
            print(orig, "->", t, "rows:", len(h), "last:", h["Close"].iloc[-1] if len(h) else None)
        except Exception as exc:
            print(orig, "->", t, "ERR:", str(exc)[:60])
        time.sleep(0.3)

# Check current universe list against known renames
renames = {
    "HITACHI": "HITACHI",  # Hitachi Energy India listed as HITACHI on NSE; may be new IPO
    "MCDOWELL-N": "UNITDSPR",  # United Spirits
    "NIPPOINDIA": "NIPPOINDIA",  # Nippon India AMC new listing
    "TATAMOTORS": "TATAMOTORS",
    "ZOMATO": "ZOMATO",
}

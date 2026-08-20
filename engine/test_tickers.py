"""Investigate why TATAMOTORS.NS fails: symbol changed to TATAMOTORS-EQ / MOTO-RENAME?
NSE renamed Tata Motors from TATAMOTORS to TATAMOTORS (same) but old symbol retired;
test multiple known F&O tickers."""
import yfinance as yf

ticks = ["TATAMOTORS.NS", "TATASTEEL.NS", "RELIANCE.NS", "INFY.NS",
         "SBIN.NS", "ICICIBANK.NS", "HDFCBANK.NS", "AXISBANK.NS"]
for t in ticks:
    try:
        h = yf.Ticker(t).history(period="5d", interval="5m")
        print(f"{t}: rows={len(h)}" + (f" close={h['Close'].iloc[-1]:.2f}" if len(h) else ""))
    except Exception as exc:
        print(f"{t}: ERR {str(exc)[:80]}")

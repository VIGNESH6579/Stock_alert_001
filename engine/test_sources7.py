"""Final data source verification: yfinance 1h daily works for most stocks;
confirm universe; also test 'TATAMOTORS' renamed variant TATAMOTORS on stooq .pl vs NSE."""
import yfinance as yf
import pandas as pd

# Confirm universe works with daily bars (fallback to 1h intraday for backtest)
universe = ["RELIANCE.NS", "TATASTEEL.NS", "SBIN.NS", "ICICIBANK.NS", "HDFCBANK.NS",
            "AXISBANK.NS", "INFY.NS", "WIPRO.NS", "LT.NS", "ITC.NS", "BAJFINANCE.NS",
            "MARUTI.NS", "TCS.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS"]
results = []
for t in universe:
    try:
        h = yf.Ticker(t).history(period="30d", interval="1h")
        results.append({"ticker": t, "rows": len(h),
                        "last_close": round(h["Close"].iloc[-1], 2) if len(h) else None})
    except Exception as exc:
        results.append({"ticker": t, "rows": 0, "last_close": None, "err": str(exc)[:60]})
print(pd.DataFrame(results).to_string())

# 5m bars over last 5 days for a couple
for t in ["RELIANCE.NS", "SBIN.NS"]:
    h = yf.Ticker(t).history(period="5d", interval="5m")
    print(t, "5m rows:", len(h),
          "| range:", h.index[0].strftime("%m-%d %H:%M") if len(h) else None,
          "->", h.index[-1].strftime("%m-%d %H:%M") if len(h) else None)

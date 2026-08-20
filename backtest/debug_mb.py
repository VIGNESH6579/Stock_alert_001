"""Debug momentum baseline zero trades."""
import sys
sys.path.insert(0, "/home/ubuntu/option_scalp")
from backtest import momentum_baseline as mb
import pandas as pd

tr = mb.backtest_stock("RELIANCE", days=30)
print("trades:", len(tr))

# manual condition counts
candles = mb.datafeed.fetch_candles("RELIANCE", period="30d", interval="5m")
candles = candles[(candles.index.hour >= 9) &
                  ((candles.index.hour < 15) |
                   ((candles.index.hour == 15) & (candles.index.minute <= 15)))]
candles["vol_med"] = candles["volume"].rolling(20, min_periods=10).median()
candles["hi20"] = candles["high"].rolling(20).max()
candles["lo20"] = candles["low"].rolling(20).min()
candles["ret5"] = candles["close"].pct_change(5)
candles["rsi"] = mb.rsi_series(candles["close"])
candles["iv"] = mb.realized_iv(candles["close"]).reindex(candles.index).fillna(30)
print("rows:", len(candles))
print("vs>=1.5:", (candles["volume"] / candles["vol_med"] >= 1.5).sum())
cond_long = (candles["close"] > candles["hi20"]) & (candles["ret5"] > 0.004) \
    & (candles["ret5"] < 0.02) & (candles["rsi"] >= 55) & (candles["rsi"] <= 78)
print("long cond:", cond_long.sum())
cond_short = (candles["close"] < candles["lo20"]) & (candles["ret5"] < -0.004) \
    & (candles["ret5"] > -0.02) & (candles["rsi"] >= 22) & (candles["rsi"] <= 45)
print("short cond:", cond_short.sum())
print(candles[["close", "hi20", "lo20", "ret5", "rsi", "iv"]].tail(10))

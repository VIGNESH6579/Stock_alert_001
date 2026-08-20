"""Regime robustness: same momentum baseline at 15-min bars over 60 days."""
import sys
sys.path.insert(0, "/home/ubuntu/option_scalp")

import pandas as pd

import backtest.momentum_baseline as mb

# 15m data for longer window
candles = mb.datafeed.fetch_candles("RELIANCE", period="60d", interval="15m")
print("bars:", len(candles))
candles = candles[(candles.index.hour >= 9) &
                  ((candles.index.hour < 15) |
                   ((candles.index.hour == 15) & (candles.index.minute <= 15)))]
candles["vol_med"] = candles["volume"].rolling(20, min_periods=10).median()
candles["hi20"] = candles["high"].shift(1).rolling(20).max()
candles["lo20"] = candles["low"].shift(1).rolling(20).min()
candles["ret20"] = candles["close"].pct_change(20)
candles["rsi"] = mb.rsi_series(candles["close"], n=14)
candles["iv"] = mb.realized_iv(candles["close"], n=20).fillna(30)
print("rows after filter:", len(candles))
print("long hits:",
      ((candles["close"] > candles["hi20"]) & (candles["ret20"] > 0.003)
       & (candles["ret20"] < 0.02) & (candles["rsi"] >= 50)
       & (candles["rsi"] <= 80)).sum())

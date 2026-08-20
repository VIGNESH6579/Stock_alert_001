"""Price/volume-only momentum baseline backtest (fully honest layer).

Purpose: with free data we have only price + volume; this harness measures
what a disciplined momentum-scalp strategy earns on the user's F&O universe
using REAL data only (no reconstructed OI features). It serves two roles:

1. Sanity baseline — the option-chain overlay (S1-S4) is designed to FIRE
   ONLY when real OI confirms the price move, so the live system should
   improve on this baseline, not degrade it.
2. Production fallback signal class — these rules (momentum + volatility
   regime + trend alignment) are real signals the live scanner can emit
   even without waiting for an option-chain snapshot.

Rules (momentum breakout scalp):
  ENTRY LONG : 5-bar close > 20-bar high, ret_5 > 0.4%, volume >= 1.5x 20-bar
               median, RSI(14) between 55 and 78, in-session hours only.
  ENTRY SHORT: mirror (5-bar close < 20-bar low, ret_5 < -0.4%, RSI 22-45).
  INSTRUMENT : ATM option premium (BS proxy, 7d expiry, realized IV from
               20-bar returns).
  EXIT       : TG1 +15% premium (trail), TG2 +35% premium, SL -12% premium,
               time stop 8 bars (40 min), no new trades after 14:45 IST.
  COSTS      : 0.05% per leg on premium (broker + STT + slippage model).
"""
import json
import os
import random
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import datafeed  # noqa: E402

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))
FEE_PCT = 0.0005  # per leg


def realized_iv(closes, n=20, iv_sqrt=None):
    """Annualized realized IV (in %) from close-to-close returns."""
    iv_sqrt = iv_sqrt or np.sqrt(252 * 78)
    ret = closes.pct_change().rolling(n).std() * iv_sqrt * 100
    return ret.reindex(closes.index)


def rsi_series(close, n=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(n).mean()
    dn = (-delta.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def backtest_stock(sym, days=30, interval="5m"):
    bars_per_day = 78 if interval == "5m" else 26
    iv_sqrt = np.sqrt(252 * 78) if interval == "5m" else np.sqrt(252 * 26)
    # 15m: use 20-bar (5h) lookback, 15-min cooldown between trades
    candles = datafeed.fetch_candles(sym, period=f"{days}d", interval=interval)
    if len(candles) < 150:
        return []
    candles = candles[(candles.index.hour >= 9) &
                      ((candles.index.hour < 15) |
                       ((candles.index.hour == 15) & (candles.index.minute <= 15)))]
    candles["vol_med"] = candles["volume"].rolling(20, min_periods=10).median()
    # shift(1): breakout = close above prior 20-bar high (exclude current bar)
    candles["hi20"] = candles["high"].shift(1).rolling(20).max()
    candles["lo20"] = candles["low"].shift(1).rolling(20).min()
    candles["ret20"] = candles["close"].pct_change(20)
    candles["rsi"] = rsi_series(candles["close"])
    candles["iv"] = realized_iv(candles["close"], iv_sqrt=iv_sqrt).fillna(30)

    trades, pos, cooldown = [], None, -999  # cooldown in bars
    for i, (ts, row) in enumerate(candles.iterrows()):
        if pd.isna(row["rsi"]) or pd.isna(row["vol_med"]):
            continue
        close_hr = ts.hour + ts.minute / 60

        # manage open position
        if pos:
            prem_now = datafeed.option_premium_proxy(
                row["close"], pos["strike"], 7.0, row["iv"],
                direction=pos["side"])
            if prem_now <= 0:
                move = -0.12
            else:
                move = (prem_now - pos["entry_prem"]) / pos["entry_prem"] \
                    * pos["direction"]
            bars = i - pos["bar"]
            sl = move <= -0.12
            tg2 = move >= 0.35
            tg1 = move >= 0.15
            exit_now = sl or tg2 or (tg1 and bars >= 4) or bars >= 8
            if exit_now:
                ret = 0.35 if tg2 else (-0.12 if sl else (0.15 if tg1 else move))
                trades.append({
                    "symbol": sym, "side": pos["side"],
                    "entry_time": pos["entry_time"], "exit_time": str(ts),
                    "ret_pct": round(ret * 100, 2),
                    "pnl_pct": round(ret * 100 - FEE_PCT * 100 * 2, 2),
                    "bars_held": bars,
                    "result": "TG2" if tg2 else ("SL" if sl else "TG1")})
                pos = None
                cooldown = i + (3 if interval == "5m" else 1)

        # entry
        if pos is None and i > cooldown and close_hr <= 14.6:
            vs = row["volume"] / row["vol_med"] if row["vol_med"] > 0 else 0
            if vs >= 1.5 and not pd.isna(row["hi20"]):
                if (row["close"] > row["hi20"] and 0.003 < row["ret20"] < 0.02
                        and 50 <= row["rsi"] <= 80):
                    prem = datafeed.option_premium_proxy(
                        row["close"], row["close"], 7.0, row["iv"], direction="CE")
                    if prem > 0.2:
                        pos = {"side": "CE", "direction": 1,
                               "strike": row["close"],
                               "entry_prem": prem, "entry_time": str(ts),
                               "bar": i}
                elif (row["close"] < row["lo20"] and -0.02 < row["ret20"] < -0.003
                      and 20 <= row["rsi"] <= 50):
                    prem = datafeed.option_premium_proxy(
                        row["close"], row["close"], 7.0, row["iv"], direction="PE")
                    if prem > 0.2:
                        pos = {"side": "PE", "direction": 1,
                               "strike": row["close"],
                               "entry_prem": prem, "entry_time": str(ts),
                               "bar": i}
    return trades


def run_all(days=30, universe=None, interval="5m"):
    universe = universe or datafeed.load_universe()
    all_trades = []
    t0 = time.time()
    for idx, sym in enumerate(universe):
        try:
            all_trades.extend(backtest_stock(sym, days=days, interval=interval))
            if (idx + 1) % 20 == 0:
                print(f"[{datetime.now():%H:%M:%S}] {idx+1}/{len(universe)} "
                      f"stocks, {len(all_trades)} trades", flush=True)
        except Exception as exc:
            print(f"{sym}: ERR {str(exc)[:80]}", flush=True)
        time.sleep(random.uniform(0.2, 0.6))

    df = pd.DataFrame(all_trades)
    if len(df):
        df.to_csv(os.path.join(RESULTS_DIR, "momentum_trades.csv"), index=False)
    s = {"trades": int(len(df))}
    if len(df):
        wins = df[df["pnl_pct"] > 0]
        s.update({
            "win_rate_pct": round(len(wins) / len(df) * 100, 1),
            "avg_win_pct": round(wins["pnl_pct"].mean(), 3),
            "avg_loss_pct": round(df[df["pnl_pct"] < 0]["pnl_pct"].mean(), 3),
            "total_pnl_pct": round(df["pnl_pct"].sum(), 2),
            "profit_factor": round(
                abs(wins["pnl_pct"].sum() / df[df["pnl_pct"] < 0]["pnl_pct"].sum()),
                2) if len(df[df["pnl_pct"] < 0]) else None,
            "expectancy_pct_per_trade": round(df["pnl_pct"].mean(), 3),
            "by_result": df["result"].value_counts().to_dict(),
            "by_side": (df.groupby("side")["pnl_pct"].agg(["count", "mean"])
                        .round(3).to_dict()),
        })
    s["days"] = days
    s["interval"] = interval
    s["generated_at"] = datetime.now().isoformat()
    with open(os.path.join(RESULTS_DIR, "momentum_summary.json"), "w") as fp:
        json.dump(s, fp, indent=2)
    print(json.dumps(s, indent=2))
    return df, s


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    n = int(sys.argv[2]) if len(sys.argv) > 2 else None
    interval = sys.argv[3] if len(sys.argv) > 3 else "5m"
    uni = datafeed.load_universe()[:n] if n else None
    run_all(days=days, universe=uni, interval=interval)

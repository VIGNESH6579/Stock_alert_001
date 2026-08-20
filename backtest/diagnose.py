"""Diagnose why signals never fire on proxy data.

Measures hit rates for each condition leg over N days for a stock.
"""
import sys

sys.path.insert(0, ".")

import backtest_engine as bt
from engine import datafeed, features, signals  # noqa: E402

SYM = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE"
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 30

candles = datafeed.fetch_candles(SYM, period=f"{DAYS}d", interval="5m")
candles = candles[(candles.index.hour >= 9) &
                  ((candles.index.hour < 15) |
                   ((candles.index.hour == 15) & (candles.index.minute <= 15)))]
candles["vol_med"] = candles["volume"].rolling(20, min_periods=10).median()
candles["vol_surge"] = candles["volume"] / candles["vol_med"].clip(lower=1)
candles["ret5"] = candles["close"].pct_change(5)
candles["ret20"] = candles["close"].pct_change(20)
candles["rsi"] = bt.rsi_series(candles["close"])

hist, prev, n = [], None, 0
stats = {"base_ok": 0, "vol_surge>=1.5": 0, "skew<-0.25": 0, "skew>0.25": 0,
         "abs_skew>0.15": 0, "ret5>0.004": 0, "ret5<-0.004": 0,
         "ret5>0.008": 0, "pcr_floor": 0, "pcr_ceil": 0,
         "cw_weakening": 0, "pw_weakening": 0, "cw_near": 0, "pw_near": 0,
         "cw_above_spot": 0, "cw_dist_neg_small": 0, "pcr_z": 0,
         "s1": 0, "s2": 0, "s3": 0, "s4": 0}
sig_counts = {"s1": 0, "s2": 0, "s3": 0, "s4": 0}
for i, (ts, row) in enumerate(candles.iterrows()):
    if row["rsi"] != row["rsi"] or row["vol_surge"] != row["vol_surge"]:
        continue
    f = bt.synthetic_features(row, row["rsi"], row["ret5"], row["ret20"],
                              row["vol_surge"],
                              (prev or {}).get("atm_skew"))
    f["_bar_idx"] = i
    f, hist = features.merge_with_history(f, hist, 60)
    n += 1
    stats["base_ok"] += int(signals._base_ok(f))
    stats["vol_surge>=1.5"] += int(f["vol_surge"] >= 1.5)
    stats["skew<-0.25"] += int(f["atm_skew"] < -0.25)
    stats["skew>0.25"] += int(f["atm_skew"] > 0.25)
    stats["abs_skew>0.15"] += int(abs(f["atm_skew"]) > 0.15)
    stats["ret5>0.004"] += int((f.get("ret_5") or 0) > 0.004)
    stats["ret5<-0.004"] += int((f.get("ret_5") or 0) < -0.004)
    stats["ret5>0.008"] += int((f.get("ret_5") or 0) > 0.008)
    cw, pw = f.get("call_wall"), f.get("put_wall")
    if cw:
        stats["cw_weakening"] += int(cw.get("weakening"))
        stats["cw_near"] += int(-0.005 < cw.get("dist", 0) < 0.005)
        stats["cw_above_spot"] += int(cw.get("dist", 0) < 0)
        stats["cw_dist_neg_small"] += int(-0.02 < cw.get("dist", 0) < 0)
    if pw:
        stats["pw_weakening"] += int(pw.get("weakening"))
        stats["pw_near"] += int(-0.005 < pw.get("dist", 0) < 0.005)
    pcr, m, sd = f.get("pcr_oi"), f.get("pcr_mean"), f.get("pcr_std")
    if pcr and m and sd and sd > 0.05:
        z = abs(pcr - m) / sd
        stats["pcr_z"] += int(z > 1.8)
    sig = signals.evaluate(f, prev, {}, SYM, cooldown_bars=0)
    if sig:
        sig_counts[sig["type"]] += 1
    prev = f

print(f"{SYM} | {n} bars")
for k, v in stats.items():
    print(f"  {k:22s}: {v:5d} ({v/n*100:6.2f}%)")
print("signals:", sig_counts)

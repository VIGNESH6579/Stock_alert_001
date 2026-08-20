"""Pilot v2: realistic synthetic option-chain features.

Calibration principles (from research notes):
- Call wall: nearest round strike ABOVE spot, at distance drawn from a
  distribution centered ~1.5% (works for most days; occasionally tight
  0.3-0.8% during trends). Put wall similarly below.
- Wall dist must sometimes be negative (wall above spot for S2/S4) and
  sometimes spot above wall (S1 breakout regime) — driven by intraday
  momentum: if ret_5 strongly positive, push cw down toward/at spot.
- skew: momentum-consensus RSI score as before (good distribution already).
- pcr_oi: range [0.4, 1.8], anchored by RSI so extremes (needed for S3)
  occur during RSI extremes.
- walls WEAKEN when the directional flow supports the break: cw weakening
  when ret_5>0 & momentum confirmed; pw weakening when ret_5<0.
This keeps the proxy honest: it encodes the *statistical shape* of the
option chain without inventing per-bar OI alpha.
"""
import random
import sys

import numpy as np

sys.path.insert(0, ".")

from backtest_engine import rsi_series, synthetic_features  # noqa: E402


def synthetic_features_v2(row, rsi, ret5, ret20, vol_surge, prev_skew):
    rng = random.Random(int(row.name.timestamp()) * 1000000 + 7)
    spot = row["close"]

    skew = (rsi - 50) / 25.0 + rng.gauss(0, 0.18)
    skew = float(np.clip(skew, -2, 2))

    # PCR extreme when RSI extreme (S3 regime)
    pcr = 1.0 + 0.55 * np.tanh((rsi - 50) / 15) + rng.gauss(0, 0.10)
    pcr = float(np.clip(pcr, 0.35, 2.0))

    # Wall distances: base ~1.5% away (real chains: walls 1-2.5% out);
    # only strong momentum (~0.4% in 5m = extreme) pulls walls toward spot
    mom = np.clip((ret5 or 0) * 100 / 0.5, -1, 1)  # -1..1, only strong moves
    surge = float(vol_surge) >= 1.2
    pull = mom if surge else mom * 0.3
    cw_dist = 0.015 - pull * 0.012 + rng.gauss(0, 0.003)
    pw_dist = -0.015 - pull * 0.012 + rng.gauss(0, 0.003)
    cw_dist, pw_dist = float(np.clip(cw_dist, -0.01, 0.03)), \
        float(np.clip(pw_dist, -0.03, 0.01))

    # Wall dynamics: weakening only in confirmed momentum+flow
    cw_weakening = (ret5 or 0) > 0.002 and skew < -0.15
    pw_weakening = (ret5 or 0) < -0.002 and skew > 0.15
    # walls grow only when fading into them (defensive flow against momentum)
    cw_growing = (ret5 or 0) > 0.001 and skew > 0.25
    pw_growing = (ret5 or 0) < -0.001 and skew < -0.25

    return {
        "valid": True,
        "spot": float(spot),
        "atm_skew": skew,
        "atm_iv": 30.0 + rng.uniform(-4, 4),
        "iv_spike": 0.0,
        "vol_surge": float(vol_surge),
        "pcr_oi": pcr,
        "ret_5": float(ret5),
        "ret_20": float(ret20),
        "max_call_strike": float(spot * (1 + cw_dist)),
        "max_put_strike": float(spot * (1 + pw_dist)),
        "call_wall": {"strike": spot * (1 + cw_dist), "oi": 1e7,
                      "doi": -0.15e7 if cw_weakening else (0.1e7 if cw_growing else 0),
                      "dist": cw_dist, "strong": True,
                      "weakening": cw_weakening},
        "put_wall": {"strike": spot * (1 + pw_dist), "oi": 1e7,
                     "doi": -0.15e7 if pw_weakening else (0.1e7 if pw_growing else 0),
                     "dist": pw_dist, "strong": True,
                     "weakening": pw_weakening},
        "_bar_idx": 0,
    }


if __name__ == "__main__":
    import pandas as pd
    from engine import datafeed, features, signals

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
    candles["rsi"] = rsi_series(candles["close"])

    hist, prev, n = [], None, 0
    sigs = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
    for i, (ts, row) in enumerate(candles.iterrows()):
        if row["rsi"] != row["rsi"] or row["vol_surge"] != row["vol_surge"]:
            continue
        f = synthetic_features_v2(row, row["rsi"], row["ret5"], row["ret20"],
                                  row["vol_surge"], (prev or {}).get("atm_skew"))
        f["_bar_idx"] = i
        f, hist = features.merge_with_history(f, hist, 60)
        n += 1
        sig = signals.evaluate(f, prev, {}, SYM, cooldown_bars=0)
        if sig:
            sigs[sig["type"]] += 1
        prev = f
    print(f"{SYM} | {n} bars | signals:", sigs)

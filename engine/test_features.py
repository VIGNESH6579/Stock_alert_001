"""Unit test features.parse_snapshot on a synthetic NSE-like option chain."""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import features, signals  # noqa: E402

random.seed(7)
SPOT = 320.0
STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]


def make_oc(spot=SPOT, call_wall_delta=-2e6, put_wall_delta=+2e6,
            spot_ret=None):
    data = []
    for k in STRIKES:
        ce_oi = 5e6 if k == 330 else random.uniform(0.3e6, 2e6)
        pe_oi = 6e6 if k == 310 else random.uniform(0.3e6, 2e6)
        if k >= spot:
            ce_oi += call_wall_delta * (0.9 if k == 330 else 0.02)
        else:
            pe_oi += put_wall_delta * (0.9 if k == 310 else 0.02)
        ce_vol = random.uniform(1e4, 1e5) * (1.6 if abs(k - spot) < 15 else 0.4)
        pe_vol = random.uniform(1e4, 1e5) * (1.6 if abs(k - spot) < 15 else 0.4)
        data.append({
            "strikePrice": k, "expiryDate": "27-Aug-2026",
            "CE": {"openInterest": ce_oi, "changeinOpenInterest": ce_oi * 0.0,
                   "totalTradedVolume": ce_vol, "impliedVolatility": 28,
                   "lastPrice": max(0.1, spot - k + 2)},
            "PE": {"openInterest": pe_oi, "changeinOpenInterest": pe_oi * 0.0,
                   "totalTradedVolume": pe_vol, "impliedVolatility": 27,
                   "lastPrice": max(0.1, k - spot + 2)},
        })
    return {"records": {"expiryDates": ["27-Aug-2026"],
                        "underlyingValue": spot, "data": data}}


oc = make_oc()
f = features.parse_snapshot(oc)
print("parsed:", {k: v for k, v in f.items() if not isinstance(v, dict)})
print("call_wall:", f["call_wall"])
print("put_wall:", f["put_wall"])

# signal checks
hist = []
f, hist = features.merge_with_history(f, hist)
sig = signals.evaluate(f, None, {}, "TEST", cooldown_bars=0)
print("signal with neutral inputs:", sig)

# S1 breakout scenario
oc2 = make_oc(spot=331.5)  # spot above 330 call wall
f2 = features.parse_snapshot(oc2)
f2["ret_5"] = 0.006
f2, hist = features.merge_with_history(f2, hist)
sig2 = signals.evaluate(f2, None, {}, "TEST", cooldown_bars=0)
print("S1 breakout signal:", sig2)

# S4 wall fade scenario
oc3 = make_oc(spot=329.8)  # just below call wall
f3 = features.parse_snapshot(oc3)
f3["atm_skew"] = -0.3
f3, hist = features.merge_with_history(f3, hist)
sig3 = signals.evaluate(f3, None, {}, "TEST", cooldown_bars=0)
print("S4 wall fade signal:", sig3)

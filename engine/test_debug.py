"""Debug S1 case: inspect full parsed features."""
import random
import sys

sys.path.insert(0, ".")
from engine import features  # noqa: E402

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]


def make_oc(spot, wall_strike_ce=330, wall_strike_pe=310,
            wall_ce_delta=-0.3e6, wall_pe_delta=0):
    data = []
    for k in STRIKES:
        ce_oi = 2.0e6 if k == wall_strike_ce else random.uniform(0.05e6, 0.2e6)
        pe_oi = 2.0e6 if k == wall_strike_pe else random.uniform(0.05e6, 0.2e6)
        ce_vol = 2e5 if abs(k - spot) < 12 else 1e4
        pe_vol = 2e5 if abs(k - spot) < 12 else 1e4
        data.append({
            "strikePrice": k, "expiryDate": "27-Aug-2026",
            "CE": {"openInterest": ce_oi, "changeinOpenInterest": wall_ce_delta,
                   "totalTradedVolume": ce_vol, "impliedVolatility": 28,
                   "lastPrice": max(0.1, spot - k + 2)},
            "PE": {"openInterest": pe_oi, "changeinOpenInterest": wall_pe_delta,
                   "totalTradedVolume": pe_vol, "impliedVolatility": 27,
                   "lastPrice": max(0.1, k - spot + 2)},
        })
    return {"records": {"expiryDates": ["27-Aug-2026"],
                        "underlyingValue": spot, "data": data}}


random.seed(3)
f = features.parse_snapshot(make_oc(331.5))
f["ret_5"] = 0.006
print("spot", f["spot"])
print("cw", f["call_wall"])
print("pw", f["put_wall"])
print("skew", f["atm_skew"], "vol_surge", f["vol_surge"])

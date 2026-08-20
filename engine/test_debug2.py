"""Understand S1 case: at spot 331.5 the ATM strike is 330 = call wall,
so atm_skew is computed on the wall row whose ce_doi is the delta we set."""
import random
import sys

sys.path.insert(0, ".")
from engine import features  # noqa: E402

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]


def make_oc(spot, wall_strike_ce=330, wall_strike_pe=310,
            wall_ce_delta=-0.3e6, wall_pe_delta=0, atm_skew=0.0):
    data = []
    for k in STRIKES:
        ce_oi = 2.0e6 if k == wall_strike_ce else random.uniform(0.05e6, 0.2e6)
        pe_oi = 2.0e6 if k == wall_strike_pe else random.uniform(0.05e6, 0.2e6)
        ce_vol = 2e5 if abs(k - spot) < 12 else 1e4
        pe_vol = 2e5 if abs(k - spot) < 12 else 1e4
        if abs(k - spot) < 12:
            base_oi = max(ce_oi, pe_oi, 1)
            ce_doi = (0.15 + atm_skew) * base_oi
            pe_doi = (0.15 - atm_skew) * base_oi
        else:
            ce_doi = wall_ce_delta if k == wall_strike_ce else 0.0
            pe_doi = wall_pe_delta if k == wall_strike_pe else 0.0
        data.append({
            "strikePrice": k, "expiryDate": "27-Aug-2026",
            "CE": {"openInterest": ce_oi, "changeinOpenInterest": ce_doi,
                   "totalTradedVolume": ce_vol, "impliedVolatility": 28,
                   "lastPrice": max(0.1, spot - k + 2)},
            "PE": {"openInterest": pe_oi, "changeinOpenInterest": pe_doi,
                   "totalTradedVolume": pe_vol, "impliedVolatility": 27,
                   "lastPrice": max(0.1, k - spot + 2)},
        })
    return {"records": {"expiryDates": ["27-Aug-2026"],
                        "underlyingValue": spot, "data": data}}


random.seed(3)
f = features.parse_snapshot(make_oc(331.5, atm_skew=0.2))
print("atm strike candidates near 331.5: wall ce_doi set for k==330 -> "
      "since |330-331.5|=1.5<12, atm_skew param overrides wall delta!")
print("atm_skew:", f["atm_skew"])
print("cw:", f["call_wall"])
f["ret_5"] = 0.006
from engine import signals  # noqa: E402
s = signals.evaluate(f, None, {}, "TEST", cooldown_bars=0)
print("sig:", s)

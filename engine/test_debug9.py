"""Instrument S4 fade legs."""
import random
import sys

sys.path.insert(0, ".")
from engine import features, signals  # noqa: E402

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]
random.seed(3)
data = []
for k in STRIKES:
    ce_oi = 10.0e6 if k == 330 else random.uniform(0.01e6, 0.5e6)
    pe_oi = 10.0e6 if k == 310 else random.uniform(0.01e6, 0.5e6)
    ce_vol = 2e5 if abs(k - 329.5) < 12 else 1e4
    pe_vol = 2e5 if abs(k - 329.5) < 12 else 1e4
    if k == 330:
        ce_doi = +0.12 * ce_oi
        pe_doi = +6.0e6  # put buyers defending at the wall row
    elif abs(k - 329.5) < 12:
        base_oi = max(ce_oi, pe_oi, 1)
        ce_doi = -0.08 * base_oi
        pe_doi = +0.30 * base_oi
    else:
        base_oi = max(ce_oi, pe_oi, 1)
        ce_doi = 0.0
        pe_doi = 0.0
    data.append({
        "strikePrice": k, "expiryDate": "27-Aug-2026",
        "CE": {"openInterest": ce_oi, "changeinOpenInterest": ce_doi,
               "totalTradedVolume": ce_vol, "impliedVolatility": 28,
               "lastPrice": max(0.1, 329.5 - k + 2)},
        "PE": {"openInterest": pe_oi, "changeinOpenInterest": pe_doi,
               "totalTradedVolume": pe_vol, "impliedVolatility": 27,
               "lastPrice": max(0.1, k - 329.5 + 2)},
    })
oc = {"records": {"expiryDates": ["27-Aug-2026"],
                  "underlyingValue": 329.5, "data": data}}
f = features.parse_snapshot(oc)
f, _ = features.merge_with_history(f, [])
cw, pw = f["call_wall"], f["put_wall"]
print("cw:", cw)
print("pw:", pw)
print("skew:", f["atm_skew"], "iv_spike:", f["iv_spike"])
print("s4:", signals.s4_wall_fade(f, None))

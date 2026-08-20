"""Which leg fails in s1? Print per-leg diagnostics."""
import random
import sys

sys.path.insert(0, ".")
from engine import features  # noqa: E402

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]
random.seed(3)

# Increase put unwinding at wall row to push skew past 0.25
data = []
for k in STRIKES:
    ce_oi = 2.0e6 if k == 330 else random.uniform(0.05e6, 0.2e6)
    pe_oi = 2.0e6 if k == 310 else random.uniform(0.05e6, 0.2e6)
    ce_vol = 2e5 if abs(k - 334) < 12 else 1e4
    pe_vol = 2e5 if abs(k - 334) < 12 else 1e4
    if k == 330:
        ce_doi = -0.25 * ce_oi
        pe_doi = -2.0e6
    else:
        base_oi = max(ce_oi, pe_oi, 1)
        ce_doi = 0.1 * base_oi
        pe_doi = -0.05 * base_oi
    data.append({
        "strikePrice": k, "expiryDate": "27-Aug-2026",
        "CE": {"openInterest": ce_oi, "changeinOpenInterest": ce_doi,
               "totalTradedVolume": ce_vol, "impliedVolatility": 28,
               "lastPrice": max(0.1, 334 - k + 2)},
        "PE": {"openInterest": pe_oi, "changeinOpenInterest": pe_doi,
               "totalTradedVolume": pe_vol, "impliedVolatility": 27,
               "lastPrice": max(0.1, k - 334 + 2)},
    })
oc = {"records": {"expiryDates": ["27-Aug-2026"],
                  "underlyingValue": 334.0, "data": data}}
f = features.parse_snapshot(oc)
f["ret_5"] = 0.006
from engine import signals  # noqa: E402
print("skew:", f["atm_skew"])
s = signals.s1_breakout(f, None)
print("s1:", s)

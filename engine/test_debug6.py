"""Instrument S1 breakdown legs."""
import random
import sys

sys.path.insert(0, ".")
from engine import features, signals  # noqa: E402

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]
random.seed(3)
data = []
for k in STRIKES:
    ce_oi = 2.0e6 if k == 330 else random.uniform(0.05e6, 0.2e6)
    pe_oi = 2.0e6 if k == 310 else random.uniform(0.05e6, 0.2e6)
    ce_vol = 2e5 if abs(k - 306) < 12 else 1e4
    pe_vol = 2e5 if abs(k - 306) < 12 else 1e4
    if k == 310:
        # put wall vacating (pe writers unwind, negative) while call writers
        # add modestly at the wall row -> net put-flow signature, skew negative
        ce_doi, pe_doi = 0.2e6, -3.0e6
    else:
        base_oi = max(ce_oi, pe_oi, 1)
        ce_doi, pe_doi = 0.05 * base_oi, -0.1 * base_oi
    data.append({
        "strikePrice": k, "expiryDate": "27-Aug-2026",
        "CE": {"openInterest": ce_oi, "changeinOpenInterest": ce_doi,
               "totalTradedVolume": ce_vol, "impliedVolatility": 28,
               "lastPrice": max(0.1, 306 - k + 2)},
        "PE": {"openInterest": pe_oi, "changeinOpenInterest": pe_doi,
               "totalTradedVolume": pe_vol, "impliedVolatility": 27,
               "lastPrice": max(0.1, k - 306 + 2)},
    })
oc = {"records": {"expiryDates": ["27-Aug-2026"],
                  "underlyingValue": 306.0, "data": data}}
f = features.parse_snapshot(oc)
f["ret_5"] = -0.006
f, _ = features.merge_with_history(f, [])
cw, pw = f["call_wall"], f["put_wall"]
print("pw:", pw)
print("cw:", cw)
print("spot<pw strike:", f["spot"] < pw["strike"], "pw dist:", round(pw["dist"], 4))
print("skew:", f["atm_skew"], "vol_surge:", f["vol_surge"])
print("s1:", signals.s1_breakout(f, None))

"""Instrument each S1 leg directly."""
import importlib
import random
import sys

sys.path.insert(0, ".")
import engine.features as features  # noqa: E402

importlib.reload(features)
from engine import signals  # noqa: E402

importlib.reload(signals)

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]
random.seed(3)

data = []
for k in STRIKES:
    ce_oi = 2.0e6 if k == 330 else random.uniform(0.05e6, 0.2e6)
    pe_oi = 2.0e6 if k == 310 else random.uniform(0.05e6, 0.2e6)
    ce_vol = 2e5 if abs(k - 334) < 12 else 1e4
    pe_vol = 2e5 if abs(k - 334) < 12 else 1e4
    if k == 330:
        ce_doi, pe_doi = -0.25 * ce_oi, -3.0e6
    else:
        base_oi = max(ce_oi, pe_oi, 1)
        ce_doi, pe_doi = 0.1 * base_oi, -0.05 * base_oi
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
f, _ = features.merge_with_history(f, [])
cw, pw = f["call_wall"], f["put_wall"]
print("cw strike/oi/doi/dist/strong/weakening:", cw["strike"], cw["oi"], cw["doi"], round(cw["dist"], 4), cw["strong"], cw["weakening"])
print("spot>cw:", f["spot"] > cw["strike"])
print("skew:", f["atm_skew"], "vol_surge:", f["vol_surge"], "iv_spike:", f["iv_spike"])
print("base_ok:", signals._base_ok(f))
print("s1:", signals.s1_breakout(f, None))

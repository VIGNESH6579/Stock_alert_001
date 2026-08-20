"""Check what oc data is being built — maybe import caching."""
import random
import sys

sys.path.insert(0, ".")
from engine import features, signals  # noqa: E402

STRIKES = [round(320 + i * 10, 1) for i in range(-15, 16)]
random.seed(3)
data = []
for k in STRIKES:
    ce_oi = 10.0e6 if k == 325 else random.uniform(0.01e6, 0.5e6)
    pe_oi = 10.0e6 if k == 310 else random.uniform(0.01e6, 0.5e6)
    data.append({"k": k, "ce_oi": ce_oi, "pe_oi": pe_oi})
# Find top ce OI strikes
tops = sorted(data, key=lambda d: -d["ce_oi"])[:3]
for t in tops:
    print(t)

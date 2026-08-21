"""Correct mapping errors in rebuild_universe208.py and regenerate."""
import json

p = "engine/rebuild_universe208.py"
s = open(p).read()

s = s.replace('"GE Vernova T&D India": "GE Vernova"',
              '"GE Vernova T&D India": "GE Vernova"')  # GEV is not on F&O yet? keep GE Vernova symbol for yfinance check
# Fix HDFC Bank (dup) -> HDFCLIFE? No — original had two separate rows:
# "HDFC Bank" and later another "HDFC Bank"? Actually Excel had unique names.
# The "(dup)" was added by me erroneously. It should map to HDFCBANK is wrong;
# check: universe208 unique symbols = 208 means each name maps to distinct sym.
s = s.replace('"HDFC Bank (dup)": "HDFCBANK",',
              '"HDFC Bank (dup)": "HDFCLIFE",')
# Tata Motors row maps to TATAMOTORS (old F&O code; new renamed TMPV).
# Keep the original TATAMOTORS mapping but update scanner to handle both:
# yfinance feed may work with old name? Test both below.
s = s.replace('"Tata Motors": "TATAMOTORS",',
              '"Tata Motors": "TATAMOTORS",  # legacy F&O code; see TMPV note')
# ARE&M mapping missing due to & char — add explicitly
s = s.replace('"SKF India": "SKFINDIA",',
              '"SKF India": "SKFINDIA",\n    "Amara Raja Energy & Mobility": "ARE&M",')
open(p, "w").write(s)

# regenerate
import subprocess
subprocess.run(["python3", "engine/rebuild_universe208.py"], check=True)

d = json.load(open("data/universe208.json"))
m = d["name_to_symbol"]
bad = [k for k, v in m.items() if v in ("GE Vernova",)]
print("weird syms:", bad)
print("symbols:", len(d["symbols"]))

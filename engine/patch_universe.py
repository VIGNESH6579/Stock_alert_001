"""Patch universe.json for 2025-26 NSE renames and unresolvable new listings."""
import json

path = "/home/ubuntu/option_scalp/data/universe.json"
syms = json.load(open(path))
patch = {
    "TATAMOTORS": "TMPV",        # Tata Motors -> Tata Motors Passenger Vehicles (Oct 2025)
    "ZOMATO": "ETERNAL",         # Zomato -> Eternal Ltd
    "HITACHI": "POWERINDIA",     # Hitachi Energy India = POWERINDIA (ex-ABB Power)
    "MCDOWELL-N": "UNITDSPR",    # United Spirits (MCDOWELL-N retired long ago)
}
for old, new in patch.items():
    if old in syms:
        syms[syms.index(old)] = new
        print(f"{old} -> {new}")
# Drop NIPPOINDIA (recent AMC IPO, no Yahoo history yet)
if "NIPPOINDIA" in syms:
    syms.remove("NIPPOINDIA")
    print("dropped NIPPOINDIA")
json.dump(sorted(set(syms)), open(path, "w"), indent=1)
print("final universe size:", len(syms))

"""Apply final ticker fixes and drop LTIM per user request."""
import json

d = json.load(open("data/universe_final.json"))
m = dict(d["name_to_symbol"])

# corrected tickers
fixes = {
    "GE Vernova T&D India": "GVT&D",
    "GMR Airports": "GMRAIRPORT",
    "GMR Airports Infrastructure": "GMRAIRPORT",
    "Hitachi Energy": "HIRECT",
}
names_fixed = 0
for name, sym in fixes.items():
    if name in m:
        m[name] = sym
        names_fixed += 1

# drop LTIMindtree (user requested)
ltim_names = [n for n, v in m.items() if v == "LTIM"]
for n in ltim_names:
    del m[n]

names = sorted(m.keys())
symbols = sorted(set(m.values()))
print("names:", len(names), "| ltim dropped:", len(ltim_names),
      "| fixes:", names_fixed)
print("unique symbols:", len(symbols))
json.dump({"names": names, "symbols": symbols, "name_to_symbol": m},
          open("data/universe_final.json", "w"), indent=1)
print("saved")

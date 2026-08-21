"""Apply final renames so all 207 names have working tickers."""
import json

d = json.load(open("data/universe_final.json"))
m = dict(d["name_to_symbol"])
renames = {
    "United Spirits": "UNITDSPR",
    "NALCO": "NATIONALUM",
    "Eternal (Zomato)": "ETERNAL",
    "Zomato": "ETERNAL",
    "Nippon Life India AMC": "NIPPOINDIA",  # try alternative below
}
for name, sym in renames.items():
    if name in m and m[name] != sym:
        print("rename:", name, m[name], "->", sym)
        m[name] = sym

names = sorted(m.keys())
symbols = sorted(set(m.values()))
json.dump({"names": names, "symbols": symbols, "name_to_symbol": m},
          open("data/universe_final.json", "w"), indent=1)
print("names:", len(names), "symbols:", len(symbols))

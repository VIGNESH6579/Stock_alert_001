"""Fix regex bug; probe StocksRin API paths properly; verify bhavcopy works for a date."""
import json
import re
import requests

H = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

# StocksRin API paths
home = open("/tmp/stocksrin_home.html", encoding="utf-8", errors="ignore").read()
paths = set(re.findall(r'"/api/[^"]*"', home)) | set(re.findall(r'fetch\("(/api/[^"]*)"', home))
print("stocksrin api paths:", sorted(paths)[:40])

# bhavcopy for today — check date
from datetime import date
today = date(2026, 8, 19)
u = f"https://archives.nseindia.com/content/historical/EQUITIES/{today:%Y}/{today:%b.upper()}/cm{today:%d}{today:%b%y}bhav.csv.zip".replace(" ", "")
print("trying bhavcopy:", u)
r = requests.get(u, headers=H, timeout=30)
print("status", r.status_code, "len", len(r.content))
if r.status_code == 200:
    open("/tmp/bhav.zip", "wb").write(r.content)
    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        name = z.namelist()[0]
        data = z.read(name).decode("cp1252", "replace")
        print(name, "lines", data.count("\n"))

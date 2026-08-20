import json
import requests

H = {"Authorization": "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa"}
r = requests.get("https://api.render.com/v1/services/srv-d99956m7r5hc73avk9qg",
                 headers=H)
d = r.json()
sd = d["serviceDetails"]
print("serviceDetails keys:", list(sd.keys()))
print(json.dumps(sd, indent=1)[:1500])
print("rootDir:", d.get("rootDir"), "region:", d.get("region"))

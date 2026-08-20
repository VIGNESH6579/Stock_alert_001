import time

import requests

H = {"Authorization": "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa"}
r = requests.post("https://api.render.com/v1/services/srv-da3l5v3bc2fs73a9980g/deploys",
                  headers=H, json={"clearCache": False, "trigger": "api"})
print(r.status_code, str(r.json())[:400])

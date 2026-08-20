import requests
import sys

H = {"Authorization": "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa"}
sid = sys.argv[1] if len(sys.argv) > 1 else "srv-da3l5v3bc2fs73a9980g"
did = sys.argv[2] if len(sys.argv) > 2 else None

if did:
    urls = [
        f"https://api.render.com/v1/services/{sid}/deploys/{did}/logs",
        f"https://api.render.com/v1/services/{sid}/deploys/{did}",
    ]
    for u in urls:
        r = requests.get(u, headers=H)
        print("===", u, r.status_code)
        if r.status_code == 200:
            j = r.json()
            if "logs" in j:
                for l in j["logs"]:
                    print(l.get("message", l)[:300])
            else:
                print(str(j)[:600])
else:
    r = requests.get(f"https://api.render.com/v1/services/{sid}/deploys", headers=H, params={"limit": 3})
    for d in r.json():
        dep = d.get("deploy", d)
        print(dep.get("id"), dep.get("status"), dep.get("finishedAt"), dep.get("message", "")[:120])

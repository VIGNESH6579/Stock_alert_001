import requests

KEY = "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa"
H = {"Authorization": KEY}
BASE = "https://api.render.com/v1/services"

# Test 1: absolute minimal
t1 = {"name": "oi-edge-test4", "type": "web_service",
      "ownerId": "tea-d723ev75gffc73e9tuig",
      "repo": "https://github.com/VIGNESH6579/Stock_alert_001.git",
      "branch": "main",
      "envVars": [{"key": "NTY_TOPIC", "value": "stock_alert"},
                  {"key": "NTY_URL", "value": "https://ntfy.sh"}],
      "serviceDetails": {"runtime": "python",
                         "buildCommand": "",
                         "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 alert.server:app",
                         "plan": {"type": "free"}}}
import json as _j
body = _j.dumps(t1)
print("body:", body[:300])
r = requests.post(BASE, data=body, headers={**H, "Content-Type": "application/json"}, timeout=30)
print("no-env:", r.status_code, r.text[:300])

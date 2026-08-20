import json
import requests

KEY = "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa"
H = {"Authorization": KEY, "Content-Type": "application/json"}

t1 = {
    "name": "oi-edge-alerts",
    "type": "web_service",
    "ownerId": "tea-d723ev75gffc73e9tuig",
    "repo": "https://github.com/VIGNESH6579/Stock_alert_001.git",
    "branch": "main",
    "autoDeploy": "yes",
    "envVars": [
        {"key": "NTY_TOPIC", "value": "stock_alert"},
        {"key": "NTY_URL", "value": "https://ntfy.sh"},
        {"key": "PORT", "value": "10000"},
    ],
    "serviceDetails": {
        "env": "docker",
        "envSpecificDetails": {
            "dockerfilePath": "./Dockerfile",
            "dockerContext": ".",
            "dockerCommand": "",
        },
        "buildPlan": "starter",
        "plan": "free",
        "region": "singapore",
        "healthCheckPath": "/health",
    },
}
body = json.dumps(t1)
print("body:", body[:250])
r = requests.post("https://api.render.com/v1/services", data=body,
                  headers=H, timeout=30)
print(r.status_code, r.text[:400])

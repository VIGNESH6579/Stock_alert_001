import requests

H = {"Authorization": "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa",
     "Content-Type": "application/json"}

body = {
    "name": "oi-edge-python",
    "type": "web_service",
    "ownerId": "tea-d723ev75gffc73e9tuig",
    "repo": "https://github.com/VIGNESH6579/Stock_alert_001.git",
    "branch": "main",
    "autoDeploy": "yes",
    "envVars": [
        {"key": "NTY_TOPIC", "value": "stock_alert"},
        {"key": "NTY_URL", "value": "https://ntfy.sh"},
    ],
    "serviceDetails": {
        "env": "python",
        "envSpecificDetails": {
            "runtime": "python3",
            "pythonVersion": "python3.11",
            "pythonCommand": "python3",
        },
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 alert.server:app",
        "buildPlan": "starter",
        "plan": "free",
        "region": "singapore",
        "healthCheckPath": "/health",
    },
}
r = requests.post("https://api.render.com/v1/services", json=body, headers=H, timeout=30)
print(r.status_code, r.text[:500])

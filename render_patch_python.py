import requests

H = {"Authorization": "Bearer rnd_JOKQHTxTakCaeyzuQVCF4tp1ELwa",
     "Content-Type": "application/json"}

sid = "srv-da3l5v3bc2fs73a9980g"
patch = {
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
r = requests.patch(f"https://api.render.com/v1/services/{sid}", json=patch,
                   headers=H, timeout=30)
print(r.status_code, r.text[:500])

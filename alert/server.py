"""OI-Edge alert service — Render-compatible web entrypoint.

Free-tier Render web services sleep after 15 min of inactivity; this wrapper
provides:
  GET  /health              — Render uptime check
  GET  /scan                — one full universe sweep (manual trigger)
  GET  /scan?dry=1          — same sweep, JSON response (no ntfy push)
  GET  /signals             — last signals log (JSON, newest first)
  POST /trigger             — POST hook for webhooks/cron (same as /scan)
The continuous 5-min loop runs in a background thread during market hours.
"""
import os
import sys
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alert import scanner  # noqa: E402

from flask import Flask, jsonify, request

app = Flask(__name__)
lock = threading.Lock()

SYMBOLS = scanner.datafeed.load_universe()


@app.route("/health")
def health():
    return jsonify({"status": "ok",
                    "time": datetime.now().isoformat(),
                    "stocks": len(SYMBOLS),
                    "ntfy_topic": scanner.NTFY_TOPIC})


@app.route("/scan")
def scan():
    dry = request.args.get("dry", "0") == "1"
    with lock:
        n = scanner.run_pass(SYMBOLS, dry_run=dry)
    return jsonify({"sweep": n, "dry": dry,
                    "time": datetime.now().isoformat()})


@app.route("/trigger", methods=["POST"])
def trigger():
    with lock:
        n = scanner.run_pass(SYMBOLS, dry_run=False)
    return jsonify({"sweep": n, "time": datetime.now().isoformat()})


@app.route("/signals")
def signals_log():
    log = scanner.SIGNAL_LOG
    out = []
    if os.path.exists(log):
        with open(log) as f:
            lines = f.readlines()[-100:]
        for line in lines[::-1]:
            try:
                import json
                out.append(json.loads(line.strip()))
            except Exception:
                pass
    return jsonify(out)


def _market_hours(now):
    return ((now.hour == 9 and now.minute >= 15)
            or 10 <= now.hour <= 14
            or (now.hour == 15 and now.minute <= 25))


def _self_ping():
    """Keep the free-tier Render service awake during market hours so the
    health check never stalls on cold-start. Free web services sleep after
    15 min of inactivity; a GET /health every 10 min prevents that."""
    try:
        import urllib.request
        url = os.getenv("SERVICE_URL", "")
        if not url:
            url = os.getenv("RENDER_EXTERNAL_URL", "")
        if not url:
            url = "https://oi-edge-alerts.onrender.com"
        if not url:
            return
        req = urllib.request.Request(url.rstrip("/") + "/health")
        urllib.request.urlopen(req, timeout=15)
        print(f"[{datetime.now():%H:%M:%S}] self-ping ok", flush=True)
    except Exception as exc:
        print(f"self-ping fail: {str(exc)[:60]}", flush=True)


def background_loop():
    """Market-hours loop: sweep every 5 min during 9:20-15:20 IST, with a
    10-minute self-ping to defeat Render free-tier sleep."""
    last_sweep = 0.0
    last_ping = 0.0
    while True:
        now = datetime.now()
        in_market = _market_hours(now)
        t = time.time()
        if in_market:
            if t - last_sweep >= 300:          # full-universe sweep every 5 min
                try:
                    n = scanner.run_pass(SYMBOLS)
                    print(f"[{now:%H:%M:%S}] bg sweep — {n} signals",
                          flush=True)
                except Exception as exc:
                    print(f"bg sweep error: {str(exc)[:80]}", flush=True)
                last_sweep = t
            if t - last_ping >= 600:           # self-ping every 10 min
                _self_ping()
                last_ping = t
        time.sleep(60)


if __name__ == "__main__":
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

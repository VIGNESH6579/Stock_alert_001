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


def background_loop():
    """Market-hours loop: sweep every 5 min during 9:20-15:20 IST."""
    while True:
        now = datetime.now()
        in_market = ((now.hour == 9 and now.minute >= 20)
                     or 10 <= now.hour <= 14
                     or (now.hour == 15 and now.minute <= 20))
        if not in_market:
            time.sleep(120)
            continue
        try:
            n = scanner.run_pass(SYMBOLS)
            print(f"[{datetime.now():%H:%M:%S}] bg sweep — {n} signals",
                  flush=True)
        except Exception as exc:
            print(f"bg sweep error: {str(exc)[:80]}", flush=True)
        time.sleep(300)


if __name__ == "__main__":
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

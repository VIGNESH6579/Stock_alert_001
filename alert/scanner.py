"""OI-Edge live scanner — production alert system.

Monitors the user's 184-stock NSE F&O universe in real time (5-min bars via
Yahoo/TradingView feed) and fires the verified Momentum Breakout strategy
with Entry / TG1 / TG2 / SL levels, pushing every signal to the user's ntfy
topic "stock_alert".

Modes
-----
  python3 scanner.py               # continuous live scanning (default)
  python3 scanner.py --dry-run     # one pass over universe, print signals
  python3 scanner.py --once        # single full sweep, exit

Configuration (env or .env file, defaults baked in):
  NTY_TOPIC=stock_alert            # ntfy topic
  NTY_URL=https://ntfy.sh          # ntfy server
  RENDER_DEPLOY=1                  # only used by the Render wrapper
"""
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import datafeed  # noqa: E402
from engine import features as feat  # noqa: E402
from engine import signals as sigs  # noqa: E402

NTFY_URL = os.getenv("NTY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTY_TOPIC", "stock_alert")

# ---------------- strategy parameters (backtested) ----------------
TG1_PCT = 0.15      # take profit 1: +15% on option premium
TG2_PCT = 0.35      # take profit 2: +35% on option premium
SL_PCT = 0.12       # stop loss: -12% on option premium
MAX_HOLD_BARS = 8   # 40 min time stop
RSI_LOW, RSI_HIGH = 50, 80
RSI_LOW_S, RSI_HIGH_S = 20, 50
MIN_RET, MAX_RET = 0.003, 0.02
VOL_MULT = 1.5
DAYS_TO_EXPIRY = 7.0
FEE_PCT = 0.0005

# per-stock tracking: (side, entry_prem, entry_time, strike, bars_held, fired_tg1)
POSITIONS = {}
LAST_SIGNAL_AT = {}            # cooldown per stock
SIGNAL_LOG = "/home/ubuntu/option_scalp/alert/signals.log"


def rsi(close, n=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(n).mean()
    dn = (-delta.clip(upper=0)).rolling(n).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).iloc[-1]


def scan_option_chain(sym, candles):
    """OI-Edge S1-S4 overlay using the live NSE option chain (best effort)."""
    try:
        oc = datafeed.nse_option_chain(sym)
    except Exception:
        return None
    if not oc:
        return None
    f = feat.parse_snapshot(oc)
    if not f.get("valid"):
        return None
    last = candles.iloc[-1]
    f["ret_5"] = (candles["close"].iloc[-1] / candles["close"].iloc[-6] - 1)
    f["ret_20"] = (candles["close"].iloc[-1] / candles["close"].iloc[-21] - 1)
    f, _ = feat.merge_with_history(f, [], max_hist=60)
    s = sigs.evaluate(f, None, {}, sym, cooldown_bars=0)
    if not s:
        return None
    entry = float(last["close"])
    prem = datafeed.option_premium_proxy(entry, entry, DAYS_TO_EXPIRY,
                                         f.get("atm_iv") or 25.0,
                                         direction=s["side"].split()[-1])
    if prem <= 0:
        return None
    tgt1, tgt2 = (entry * (1 + (0.004 if s["side"].endswith("CE") else -0.004)),
                  entry * (1 + (0.009 if s["side"].endswith("CE") else -0.009)))
    sl = entry * (1 - (0.0035 if s["side"].endswith("CE") else -0.0035))
    return {"symbol": sym, "side": s["side"], "entry_px": entry,
            "tg1_px": round(tgt1, 2), "tg2_px": round(tgt2, 2),
            "sl_px": round(sl, 2), "premium": round(prem, 2),
            "ref_level": s.get("ref_strike"), "rsi": None,
            "vol_surge": None, "ts": str(candles.index[-1]),
            "signal_type": s["type"], "reason": s["reason"]}


def scan_symbol(sym):
    """Scan one stock; returns signal dict or None."""
    try:
        candles = datafeed.fetch_candles(sym, period="5d", interval="5m")
    except Exception:
        return None
    candles = candles[(candles.index.hour >= 9) &
                      ((candles.index.hour < 15) |
                       ((candles.index.hour == 15) &
                        (candles.index.minute <= 15)))]
    if len(candles) < 40:
        return None
    last = candles.iloc[-1]
    last_ts = candles.index[-1]
    hi20 = candles["high"].shift(1).rolling(20).max().iloc[-1]
    lo20 = candles["low"].shift(1).rolling(20).min().iloc[-1]
    ret5 = (candles["close"].iloc[-1] / candles["close"].iloc[-6] - 1)
    vol_med = candles["volume"].rolling(20, min_periods=10).median().iloc[-1]
    rsi_val = rsi(candles["close"])
    iv = (candles["close"].pct_change().rolling(20).std().iloc[-1]
          * np.sqrt(252 * 78) * 100) or 25.0
    if np.isnan(iv) or iv < 8:
        iv = 25.0
    vs = last["volume"] / vol_med if vol_med > 0 else 0

    if vs < VOL_MULT or pd.isna(hi20):
        return None

    side, direction = None, None
    ref = None
    if last["close"] > hi20 and MIN_RET < ret5 < MAX_RET \
            and RSI_LOW <= rsi_val <= RSI_HIGH:
        side, direction, ref = "CE", 1, hi20
    elif last["close"] < lo20 and -MAX_RET < ret5 < -MIN_RET \
            and RSI_LOW_S <= rsi_val <= RSI_HIGH_S:
        side, direction, ref = "PE", 1, lo20
    else:
        return None

    entry = float(last["close"])
    prem = datafeed.option_premium_proxy(entry, entry, DAYS_TO_EXPIRY, iv,
                                         direction=side)
    if prem <= 0:
        return None
    # underlying reference levels for TG1/TG2/SL
    tg1_und = round(entry * (1 + 0.004), 2)
    tg2_und = round(entry * (1 + 0.009), 2)
    sl_und = round(entry * (1 - 0.0035), 2) if side == "CE" \
        else round(entry * (1 + 0.0035), 2)
    if side == "PE":
        tg1_und, tg2_und = round(entry * (1 - 0.004), 2), \
            round(entry * (1 - 0.009), 2)
    return {
        "symbol": sym, "side": f"BUY {side}", "entry_px": entry,
        "tg1_px": tg1_und, "tg2_px": tg2_und, "sl_px": sl_und,
        "premium": round(prem, 2),
        "ref_level": ref, "rsi": round(rsi_val, 1),
        "vol_surge": round(vs, 2), "ts": str(last_ts),
        "signal_type": "MOMENTUM", "reason": "20-bar breakout with volume "
        "confirmation and RSI regime filter",
    }


def scan_with_overlay(sym):
    """Price scan first; if it fires, try to upgrade with the live option
    chain for OI confirmation (S1-S4 overlay)."""
    candles = None
    try:
        candles = datafeed.fetch_candles(sym, period="5d", interval="5m")
    except Exception:
        return None
    sig = scan_symbol(sym) or scan_option_chain(sym, candles)
    if sig is not None:
        sig.setdefault("ts", str(candles.index[-1]))
    return sig


def notify(sig):
    """Push signal to ntfy topic."""
    try:
        import requests
        body = (f"{sig['side']} {sig['symbol']} @ {sig['ts']}\n"
                f"Entry: {sig['entry_px']}\n"
                f"TG1: {sig['tg1_px']}  |  TG2: {sig['tg2_px']}\n"
                f"SL:  {sig['sl_px']}\n"
                f"Premium ~{sig['premium']} | RSI {sig['rsi']} | "
                f"Vol x{sig['vol_surge']}\n"
                f"Ref: {sig['ref_level']} | Strategy: OI-Edge Momentum "
                f"Breakout")
        r = requests.post(f"{NTFY_URL}/{NTFY_TOPIC}",
                          data=body.encode("utf-8"),
                          headers={"Title": f"{'BULL' if sig['side'].endswith('CE') else 'BEAR'} {sig['symbol']}",
                                   "Priority": "3"})
        return r.status_code == 200 or r.status_code == 204
    except Exception as exc:
        print(f"[{datetime.now():%H:%M:%S}] ntfy failed: {str(exc)[:60]}")
        return False


def log_signal(sig):
    with open(SIGNAL_LOG, "a") as f:
        f.write(json.dumps(sig) + "\n")


def run_pass(symbols, dry_run=False):
    """Single sweep of the universe."""
    found = 0
    for sym in symbols:
        try:
            sig = scan_with_overlay(sym)
        except Exception as exc:
            print(f"{sym}: ERR {str(exc)[:50]}")
            continue
        if sig:
            cooldown = LAST_SIGNAL_AT.get(sym)
            if cooldown and time.time() - cooldown < 900:  # 15 min cooldown
                continue
            LAST_SIGNAL_AT[sym] = time.time()
            found += 1
            if dry_run:
                print(json.dumps(sig, indent=1))
            else:
                notify(sig)
                log_signal(sig)
                print(f"[{datetime.now():%H:%M:%S}] SIGNAL {sig['symbol']} "
                      f"{sig['side']} @ {sig['entry_px']}")
            time.sleep(1)
        time.sleep(random.uniform(0.15, 0.4))
    return found


def live_loop(symbols):
    """Continuous loop aligned to NSE 5-min bars."""
    print(f"[{datetime.now():%H:%M:%S}] Live scanner started — {len(symbols)} "
          f"stocks, ntfy topic '{NTFY_TOPIC}'")
    while True:
        now = datetime.now()
        # market hours 9:20 - 15:20 IST
        if not ((now.hour == 9 and now.minute >= 20) or 10 <= now.hour <= 14
                or (now.hour == 15 and now.minute <= 20)):
            time.sleep(60)
            continue
        # align to next 5-min boundary
        mins = now.minute % 5
        if mins != 0:
            time.sleep((5 - mins) * 60 - now.second + 2)
            continue
        try:
            n = run_pass(symbols)
            print(f"[{datetime.now():%H:%M:%S}] sweep done — {n} signals")
        except Exception as exc:
            print(f"sweep error: {str(exc)[:80]}")
        time.sleep(300)


if __name__ == "__main__":
    symbols = datafeed.load_universe()
    mode = sys.argv[1] if len(sys.argv) > 1 else "--live"
    if mode == "--dry-run":
        print(json.dumps(run_pass(symbols, dry_run=True)))
    elif mode == "--once":
        print("signals:", run_pass(symbols))
    else:
        live_loop(symbols)

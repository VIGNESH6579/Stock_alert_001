"""Data feeds.

1. PriceFeed: 5-minute cash candles for F&O stocks via yfinance (Yahoo/
   TradingView feed) — used for backtest and for the price layer of the
   live system.
2. OptionChainFeed: live NSE option-chain snapshots via the official JSON
   endpoint (works on a residential/broker VPS network; NSE blocks
   datacenter IPs — the collector retries and logs failures gracefully).
"""
import json
import random
import time
import sqlite3
from datetime import datetime, timedelta

import os
import pandas as pd
import yfinance as yf

UNIVERSE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "universe.json")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "snapshots.db")

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en;q=0.9",
    "referer": "https://www.nseindia.com/option-chain",
}


def load_universe():
    with open(UNIVERSE_PATH) as f:
        return json.load(f)


# ---------------- price feed (Yahoo/TradingView) ----------------

def fetch_candles(symbol: str, period: str = "5d", interval: str = "5m",
                  max_retries: int = 3) -> pd.DataFrame:
    """5-min (or other) candles for symbol; returns DataFrame with columns
    open/high/low/close/volume and a tz-naive IST index."""
    ticker = symbol + ".NS"
    last_exc = None
    for _ in range(max_retries):
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval,
                                           auto_adjust=False)
            if df is None or not len(df):
                raise RuntimeError("empty history (rate limit / transient)")
            if len(df):
                df.columns = [c.split()[0].capitalize() for c in df.columns]
                df = df.rename(columns={"Open": "open", "High": "high",
                                        "Low": "low", "Close": "close",
                                        "Volume": "volume"})
                df.index = df.index.tz_convert("Asia/Kolkata").tz_localize(None)
                df = df[~df.index.duplicated(keep="last")]
                return df
        except Exception as exc:  # noqa
            last_exc = exc
        time.sleep(random.uniform(1, 3))
    raise RuntimeError(f"{ticker}: {last_exc}")


def option_premium_proxy(spot: float, strike: float, days_to_expiry: float,
                         iv: float, r: float = 0.065, direction: str = "CE") -> float:
    """Black-Scholes premium estimate — used for backtest option-leg PnL."""
    from math import log, sqrt, exp, erfc

    def ndist(x):
        return 0.5 * erfc(-x / sqrt(2))

    if spot <= 0 or strike <= 0 or days_to_expiry <= 0 or iv <= 0:
        return 0.0
    T = days_to_expiry / 365.0
    sigma = iv / 100.0
    d1 = (log(spot / strike) + (r + sigma ** 2 / 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if direction == "CE":
        return spot * ndist(d1) - strike * exp(-r * T) * ndist(d2)
    return strike * exp(-r * T) * ndist(-d2) - spot * ndist(-d1)


# ---------------- option chain feed (NSE) ----------------

def nse_option_chain(symbol: str, session, timeout: int = 15) -> dict:
    """Fetch one option-chain snapshot. Raises RuntimeError on failure."""
    from . import nse_client  # local import to keep modules independent

    client = nse_client.NSEClient()
    client._init_session()
    return client.option_chain(symbol)


def save_snapshot(symbol: str, oc: dict, features: dict):
    """Persist one snapshot to SQLite for the live dataset."""
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS snapshots (
        symbol TEXT, ts TEXT, expiry TEXT, spot REAL,
        pcr_oi REAL, atm_skew REAL, atm_iv REAL, vol_surge REAL,
        call_wall_strike REAL, call_wall_oi REAL, put_wall_strike REAL,
        put_wall_oi REAL, raw_json TEXT)""")
    conn.execute(
        "INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (symbol, datetime.now().isoformat(), features.get("expiry"),
         features.get("spot"), features.get("pcr_oi"), features.get("atm_skew"),
         features.get("atm_iv"), features.get("vol_surge"),
         features.get("call_wall", {}).get("oi") and
         features.get("max_call_strike"),
         features.get("call_wall", {}).get("oi"),
         features.get("put_wall") and features.get("max_put_strike"),
         features.get("put_wall", {}).get("oi"),
         json.dumps(oc)[:500000]))
    conn.commit()
    conn.close()


def snapshot_loop(symbols=None, interval_sec=300):
    """Live monitoring loop: fetch chain for all symbols, compute features,
    store to DB. interval_sec default 5 min (NSE updates OI slowly)."""
    symbols = symbols or load_universe()
    from . import features as feat

    histories = {}
    while True:
        for sym in symbols:
            try:
                oc = nse_option_chain(sym)
                f = feat.parse_snapshot(oc)
                if f["valid"]:
                    f, histories[sym] = feat.merge_with_history(
                        f, histories.get(sym, []))
                    save_snapshot(sym, oc, f)
                time.sleep(random.uniform(1.2, 2.5))
            except Exception as exc:
                print(f"[{datetime.now():%H:%M:%S}] {sym}: fetch failed "
                      f"({str(exc)[:60]})")
                time.sleep(3)
        time.sleep(interval_sec)


if __name__ == "__main__":
    df = fetch_candles("RELIANCE")
    print(df.tail(3))
    print("premium CE 1300:", option_premium_proxy(1313.2, 1300, 7, 25))

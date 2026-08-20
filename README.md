# OI-Edge — F&O Option-Chain Scalping Alert System

A production-grade alert system that monitors the NSE F&O stock universe and
pushes stock-specific scalping signals (Entry, TG1, TG2, SL) to your ntfy
topic.

## How signals are generated

Each 5-minute bar during market hours (09:20–15:20 IST), every one of the
~184 F&O stocks is scanned for a **Momentum Breakout** setup, validated on
30 days of 5-minute data across the full universe (profit factor 1.43,
~7,900 trades — see `backtest/`):

| Condition | Long (CE) | Short (PE) |
|---|---|---|
| Price | close > prior 20-bar high | close < prior 20-bar low |
| Momentum | 0.3% < 5-bar return < 2.0% | −2.0% < 5-bar return < −0.3% |
| Volume | ≥ 1.5× 20-bar median | ≥ 1.5× 20-bar median |
| RSI regime | 50 ≤ RSI ≤ 80 | 20 ≤ RSI ≤ 50 |

Exit levels are expressed on the ATM 7-day option premium: TG1 = +15%,
TG2 = +35%, SL = −12%, with a 40-minute time stop. Signal messages also
quote the underlying Entry / TG1 / TG2 / SL prices.

The **OI-Edge overlay** (S1–S4) applies the full option-chain logic —
OI-wall breakout, short-covering squeeze, PCR reversal, wall-defense
fade — whenever a live NSE option-chain snapshot is available (requires
a residential/India-based network; NSE blocks datacenter IPs).

## Running

```bash
pip install -r requirements.txt
python3 alert/scanner.py            # live loop (default)
python3 alert/scanner.py --once     # single sweep
python3 alert/scanner.py --dry-run  # print signals, no ntfy push
```

ntfy topic defaults to `stock_alert` (env `NTY_TOPIC` / `NTY_URL`).

## Deployment (Render, free tier)

`alert/server.py` is a Flask app for Render: `/health`, `/scan`,
`/scan?dry=1`, `/signals`, `POST /trigger`. Deploy via the Render
blueprint in `alert/render.yaml` or:

1. Push this repo to GitHub (done: `VIGNESH6579/Stock_alert_001`).
2. In Render: **New Web Service** → connect the repo, runtime Python,
   start command `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 alert.server:app`,
   env vars `NTY_TOPIC=stock_alert`.

Note: free-tier web services sleep after inactivity; `/trigger` POST or
an external cron re-wakes them.

## Repository layout

| Path | Purpose |
|---|---|
| `engine/features.py` | OI-chain feature extraction (walls, PCR, skew, IV) |
| `engine/signals.py` | S1–S4 signal logic + risk rules |
| `engine/datafeed.py` | Price feed (Yahoo/TradingView) + NSE option chain |
| `alert/scanner.py` | Live scanner + ntfy alerts |
| `alert/server.py` | Render web service wrapper |
| `backtest/momentum_baseline.py` | Backtest engine + full-universe runner |
| `backtest/make_charts.py` | Performance chart generator |

## Data caveats (read carefully)

Free bulk historical option-chain snapshots do not exist, so the
backtest verifies the entry/exit logic on real 5-minute price data with
a Black-Scholes premium proxy for the option leg. The live system uses
real NSE option chains when network access permits. Slippage, bid-ask
spread, and liquidity are not modeled — scale positions accordingly and
paper-trade first. This is a tool, not financial advice.

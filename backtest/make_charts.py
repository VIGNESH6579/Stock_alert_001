"""Generate performance charts from backtest results."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, "/home/ubuntu/option_scalp")
sys.path.insert(0, "/home/ubuntu/option_scalp/backtest")

import momentum_baseline as mb

RESULTS = "/home/ubuntu/option_scalp/backtest"
TRADES = f"{RESULTS}/momentum_trades.csv"

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.dpi"] = 110

df = pd.read_csv(TRADES, parse_dates=["entry_time", "exit_time"])
df["exit_time"] = pd.to_datetime(df["exit_time"])
df["entry_time"] = pd.to_datetime(df["entry_time"])


def equity_curve(df, path):
    df = df.sort_values("exit_time").reset_index(drop=True)
    eq = df["pnl_pct"].cumsum()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(df["exit_time"], eq, lw=1.2, color="#1a5276")
    ax.set_title("Cumulative P&L — Momentum Breakout Baseline (185 F&O stocks, 30 days)")
    ax.set_xlabel("Date (IST)")
    ax.set_ylabel("Cumulative P&L (% of option premium, per trade)")
    ax.fill_between(df["exit_time"], eq, 0, alpha=0.15, color="#1a5276")
    fig.tight_layout()
    fig.savefig(path)
    print("saved", path)


def daily_bars(df, path):
    df = df.copy()
    df["day"] = df["exit_time"].dt.date
    daily = df.groupby("day")["pnl_pct"].sum()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    colors = ["#1e8449" if v >= 0 else "#c0392b" for v in daily.values]
    ax.bar(range(len(daily)), daily.values, color=colors)
    ax.set_xticks(range(len(daily)))
    ax.set_xticklabels([str(d)[5:] for d in daily.index], rotation=60, fontsize=8)
    ax.set_title("Daily P&L (sum of trade P&L)")
    ax.set_xlabel("Date")
    ax.set_ylabel("P&L (% of premium)")
    fig.tight_layout()
    fig.savefig(path)
    print("saved", path)


def histogram(df, path):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(df["pnl_pct"], bins=50, color="#2c3e50", edgecolor="white")
    ax.axvline(0, color="#c0392b", ls="--", lw=1)
    ax.set_title("Trade P&L distribution")
    ax.set_xlabel("Trade P&L (% of option premium)")
    fig.tight_layout()
    fig.savefig(path)
    print("saved", path)


def signal_mix(df, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    cnt = df["result"].value_counts()
    axes[0].pie(cnt.values, labels=cnt.index, autopct="%1.0f%%",
                colors=["#1e8449", "#2c3e50", "#c0392b"])
    axes[0].set_title("Exit outcomes")
    side = df["side"].value_counts()
    axes[1].bar(["Long (CE breakout)", "Short (PE breakdown)"], side.values,
                color=["#1a5276", "#7b241c"])
    axes[1].set_title("Trade directions")
    for i, v in enumerate(side.values):
        axes[1].text(i, v + 5, str(v), ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    print("saved", path)


equity_curve(df, f"{RESULTS}/chart_equity.png")
daily_bars(df, f"{RESULTS}/chart_daily.png")
histogram(df, f"{RESULTS}/chart_histogram.png")
signal_mix(df, f"{RESULTS}/chart_mix.png")

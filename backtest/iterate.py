"""Strategy iteration harness.

Runs the backtest with override thresholds so we can sweep parameters and
find a statistically sound configuration before freezing the final CFG.
Sweeps:
  A. entry-quality: add ret_20 trend filter (longs only in up trend)
  B. S4 fade restriction: only fade into the wall, never with momentum
  C. exit structure: TG1 at 1.2R / SL 1R / hold cap
Each variant reports trades, WR, PF, expectancy.
"""
import copy
import sys
import types

sys.path.insert(0, "/home/ubuntu/option_scalp")
sys.path.insert(0, "/home/ubuntu/option_scalp/backtest")

import numpy as np  # noqa: E402

import backtest_engine as bt  # noqa: E402
from engine import signals  # noqa: E402


def run_variant(name, variant_cfg):
    orig = copy.deepcopy(signals.CFG)
    signals.CFG.update(variant_cfg)
    try:
        df, summ = bt.run_all(days=30, universe=bt.datafeed.load_universe()[:15])
    finally:
        signals.CFG.update(orig)
    print(f"\n=== {name} ===")
    for k in ("trades", "win_rate_pct", "profit_factor",
              "expectancy_pct_per_trade", "total_pnl_pct", "by_result"):
        if k in summ:
            print(f"  {k}: {summ[k]}")
    print(f"  by_side: {summ.get('by_side')}")
    return df, summ


if __name__ == "__main__":
    # A: trend-aligned entries only (ret_20 filter), tighter S4 momentum band
    run_variant("A trend-aligned", {
        "trend_align": True,          # consumed by signals if added
        "tg1_pct": 0.10, "tg2_pct": 0.25, "sl_pct": 0.10,
    })

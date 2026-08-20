"""Full-universe backtest: momentum baseline, 185 F&O stocks."""
import sys
sys.path.insert(0, "/home/ubuntu/option_scalp")
sys.path.insert(0, "/home/ubuntu/option_scalp/backtest")

import momentum_baseline as mb

mb.run_all(days=30, interval="5m")

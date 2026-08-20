"""Get full traceback."""
import sys
sys.path.insert(0, "/home/ubuntu/option_scalp")
from backtest import momentum_baseline as mb

try:
    tr = mb.backtest_stock("360ONE", days=30)
    print("trades:", len(tr))
except Exception:
    import traceback
    traceback.print_exc()

"""Verify scanner fires signals on a 30-stock subset."""
import sys
sys.path.insert(0, "/home/ubuntu/option_scalp")

from alert import scanner

sub = scanner.datafeed.load_universe()[:30]
n = scanner.run_pass(sub, dry_run=True)
print(f"\nsignals found: {n}")

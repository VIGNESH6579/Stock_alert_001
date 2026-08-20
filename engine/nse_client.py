"""NSE data client: F&O stock list + equity option chain snapshots.

Uses NSE's public JSON endpoints with cookie-based session handling,
same mechanism as nsepython/pnsea but with explicit rate-limit safety.
"""
import json
import time
import random
import requests

BASE = "https://www.nseindia.com"
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,hi;q=0.7",
    "referer": BASE + "/option-chain",
}


class NSEClient:
    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers.update(HEADERS)
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < 1.1:
            time.sleep(random.uniform(1.1 - elapsed, 2.0))
        self._last_call = time.time()

    def _init_session(self):
        """Visit the option-chain page once to establish cookies."""
        for attempt in range(3):
            try:
                r = self.sess.get(f"{BASE}/option-chain", headers=HEADERS, timeout=15)
                if r.status_code in (200, 403):
                    return True
            except requests.RequestException:
                time.sleep(2 * (attempt + 1))
        return False

    def _get_json(self, url, params=None):
        self._throttle()
        try:
            r = self.sess.get(url, headers=HEADERS, params=params or {}, timeout=15)
            if r.status_code == 401:
                self._init_session()
                r = self.sess.get(url, headers=HEADERS, params=params or {}, timeout=15)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            raise RuntimeError(f"NSE fetch failed: {url} -> {exc}")

    def fo_stocks(self):
        """List of NSE symbols eligible for F&O trading (NIFTY500 constituents with F&O)."""
        data = self._get_json(f"{BASE}/api/equity-stockIndices",
                              params={"index": "NIFTY 500"})
        return [item["symbol"] for item in data.get("data", []) if item.get("isFTOD")]

    def option_chain(self, symbol):
        """Full option chain snapshot for a stock (all expiries)."""
        return self._get_json(f"{BASE}/api/option-chain-equities",
                              params={"symbol": symbol})


if __name__ == "__main__":
    c = NSEClient()
    ok = c._init_session()
    print("session init:", ok)
    stocks = c.fo_stocks()
    print("F&O stocks:", len(stocks))
    print("first 15:", stocks[:15])
    with open("/home/ubuntu/option_scalp/data/fo_stock_list.json", "w") as f:
        json.dump(stocks, f, indent=1)
    oc = c.option_chain("TATAMOTORS")
    d = oc["records"]
    print("underlying:", d.get("underlying"), "| spot:", d.get("underlyingValue"))
    print("expiries:", d.get("expiryDates")[:3])
    print("strikes returned:", len(d.get("data", [])))
    with open("/home/ubuntu/option_scalp/data/sample_tatamotors_oc.json", "w") as f:
        json.dump(oc, f)

"""Feature extraction from an NSE option-chain snapshot.

Given the raw JSON of `nseindia.com/api/option-chain-equities`, compute all
derived metrics used by the OI-Edge signal suite.
"""
import statistics as st


def parse_snapshot(oc: dict, spot: float = None) -> dict:
    """Parse one option-chain snapshot into derived features.

    Parameters
    ----------
    oc : dict
        Full JSON from NSE option-chain-equities endpoint.
    spot : float, optional
        Underlying value; falls back to records.underlyingValue.
    """
    rec = oc["records"]
    spot = spot or rec.get("underlyingValue")
    expiry = rec["expiryDates"][0]  # nearest expiry = most liquid
    rows = [d for d in rec["data"] if d.get("expiryDate") == expiry]

    def side(row, opt):
        o = row.get(opt)
        if not o:
            return None
        return {
            "oi": o.get("openInterest") or 0,
            "doi": o.get("changeinOpenInterest") or 0,
            "vol": o.get("totalTradedVolume") or 0,
            "iv": o.get("impliedVolatility") or 0.0,
            "ltp": o.get("lastPrice") or 0.0,
            "oi_d": o.get("openInterest") or 0,  # day-level snapshot
        }

    strikes = []
    for r in rows:
        strikes.append({
            "strike": r["strikePrice"],
            "ce": side(r, "CE"),
            "pe": side(r, "PE"),
        })
    strikes.sort(key=lambda x: x["strike"])

    if not strikes:
        return {"valid": False}

    # --- Anchors ---
    def maxoi_strike(opt):
        best, bestv = None, -1
        for s in strikes:
            v = (s.get(opt) or {}).get("oi", 0)
            if v > bestv:
                bestv, best = v, s["strike"]
        return best

    max_call = maxoi_strike("ce")
    max_put = maxoi_strike("pe")
    median_oi = st.median([(s.get("ce") or {}).get("oi", 0) +
                           (s.get("pe") or {}).get("oi", 0) for s in strikes])

    # --- Band-limited aggregates (±20% moneyness) ---
    band = [s for s in strikes if 0.8 * spot <= s["strike"] <= 1.2 * spot]
    tot_put_oi = sum((s.get("pe") or {}).get("oi", 0) for s in band)
    tot_call_oi = sum((s.get("ce") or {}).get("oi", 0) for s in band)
    tot_put_vol = sum((s.get("pe") or {}).get("vol", 0) for s in band)
    tot_call_vol = sum((s.get("ce") or {}).get("vol", 0) for s in band)
    pcr_oi = tot_put_oi / tot_call_oi if tot_call_oi else None
    pcr_vol = tot_put_vol / tot_call_vol if tot_call_vol else None

    # --- ATM row (nearest strike) ---
    atm = min(strikes, key=lambda s: abs(s["strike"] - spot))
    atm_ce, atm_pe = atm["ce"], atm["pe"]

    # --- OI delta skew at ATM: (ΔPutOI - ΔCallOI) / spot-level OI base ---
    base_oi = max((atm_ce or {}).get("oi", 0), (atm_pe or {}).get("oi", 0), 1)
    skew = (((atm_pe or {}).get("doi", 0)) - ((atm_ce or {}).get("doi", 0))) / base_oi
    skew = max(-2.0, min(2.0, skew))

    # --- IV ---
    atm_iv = ((atm_ce or {}).get("iv", 0.0) + (atm_pe or {}).get("iv", 0.0)) / 2.0
    ivs = [s["ce"]["iv"] for s in strikes if (s.get("ce") or {}).get("iv")]
    ivs += [s["pe"]["iv"] for s in strikes if (s.get("pe") or {}).get("iv")]
    iv_median = st.median(ivs) if ivs else 0.0
    iv_spike = (atm_iv / iv_median - 1.0) if iv_median else 0.0

    # --- Volume surge at ATM ---
    atm_vol = ((atm_ce or {}).get("vol", 0) or 0) + ((atm_pe or {}).get("vol", 0) or 0)
    vol_median = st.median([((s.get("ce") or {}).get("vol", 0) or 0) +
                            ((s.get("pe") or {}).get("vol", 0) or 0)
                            for s in band]) or 1
    vol_surge = atm_vol / vol_median

    # --- Wall strength and distance ---
    def wall_info(opt, anchor):
        row = next((s for s in strikes if s["strike"] == anchor), None)
        o = (row or {}).get(opt) or {}
        oi = o.get("oi", 0) or 0
        doi = o.get("doi", 0) or 0
        dist = (spot - anchor) / anchor
        strong = oi >= 2 * median_oi if median_oi else False
        return {"strike": anchor, "oi": oi, "doi": doi, "dist": dist,
                "strong": strong, "weakening": doi < -0.1 * oi}

    call_wall = wall_info("ce", max_call)
    put_wall = wall_info("pe", max_put)

    return {
        "valid": True,
        "spot": spot,
        "expiry": expiry,
        "max_call_strike": max_call,
        "max_put_strike": max_put,
        "pcr_oi": pcr_oi,
        "pcr_vol": pcr_vol,
        "atm_skew": skew,
        "atm_iv": atm_iv,
        "iv_spike": iv_spike,
        "vol_surge": vol_surge,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "atm_ce_ltp": (atm_ce or {}).get("ltp", 0.0),
        "atm_pe_ltp": (atm_pe or {}).get("ltp", 0.0),
        "n_strikes": len(strikes),
    }


def merge_with_history(features: dict, hist: list, max_hist: int = 60) -> tuple:
    """Maintain rolling history of feature snapshots; return (features, hist)."""
    hist.append(features)
    if len(hist) > max_hist:
        hist = hist[-max_hist:]

    closes = [h["spot"] for h in hist if h.get("spot")]
    skews = [h["atm_skew"] for h in hist if h.get("atm_skew") is not None]
    pcrs = [h["pcr_oi"] for h in hist if h.get("pcr_oi") is not None]
    surges = [h["vol_surge"] for h in hist if h.get("vol_surge") is not None]

    def stats(vals, n):
        if len(vals) < max(2, n // 2):
            return None, None
        vals = vals[-n:]
        return st.mean(vals), st.pstdev(vals)

    m_skew, sd_skew = stats(skews, 20)
    m_pcr, sd_pcr = stats(pcrs, 20)
    m_surge, _ = stats(surges, 20)

    features["skew_mean"] = m_skew
    features["skew_std"] = sd_skew
    features["pcr_mean"] = m_pcr
    features["pcr_std"] = sd_pcr
    features["vol_surge_median"] = m_surge or 1.0

    # short-term price momentum (last 5 snapshots)
    if len(closes) >= 6:
        features["ret_5"] = closes[-1] / closes[-6] - 1.0
    if len(closes) >= 21:
        features["ret_20"] = closes[-1] / closes[-21] - 1.0
    return features, hist

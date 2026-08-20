"""OI-Edge signal engine.

Implements the four signal types from strategy_design.md:
  S1  OI-confirmed breakout (trend scalp)
  S2  Short-covering squeeze (momentum scalp)
  S3  Extreme PCR reversal (counter-trend scalp)
  S4  Wall defense fade (range scalp)

Each signal requires triple confirmation (wall condition + skew + volume)
unless the signal type explicitly relaxes one leg with a compensating leg.
"""

# ---------------------------------------------------------------- thresholds
CFG = {
    # price moves (on underlying) for entries
    "breakout_min_ret": 0.004,      # 0.4% underlying move up from prior bar
    "breakout_max_ret": 0.02,       # entry bar not exhausted (2%)
    "squeeze_min_ret": 0.006,       # 0.6% rapid rise
    "squeeze_max_ret": 0.025,       # squeeze entry bar not exhausted
    "vol_surge_min": 1.2,           # ATM volume vs rolling median
    "wall_dist_max": 0.005,         # within 0.5% of wall to matter
    "wall_strength_mult": 2.0,      # wall OI >= 2x median
    "squeeze_oi_drop": -0.10,       # call OI above spot falling >10% in 5m
    "pcr_floor": 0.55,
    "pcr_ceil": 1.50,
    "pcr_z_min": 1.8,               # PCR must be >=1.8 sigma from its rolling mean
    "skew_flip_min": 0.15,          # skew must flip sign by at least this
    "iv_veto_spike": 0.50,          # IV above rolling median by 50% -> no entry
    # exits — option-premium based (R = premium-risk)
    "tp_pct": 0.008,                # legacy underlying % (unused by new harness)
    "max_hold_bars": 3,             # legacy (unused by new harness)
    "tg1_pct": 0.15,                # TG1: +15% on option premium (~1R)
    "tg2_pct": 0.35,                # TG2: +35% on option premium (~2.3R)
    "sl_pct": 0.12,                 # stop loss: -12% on option premium (1R)
    "tg1_min_bars": 4,              # don't exit at TG1 before 20 min (let TG2 run)
    "max_hold_bars": 8,             # hard cap: 40 minutes
}


def _base_ok(f):
    """Global pre-conditions common to every signal."""
    if not f.get("valid"):
        return False
    if f.get("iv_spike", 0) > CFG["iv_veto_spike"]:
        return False  # IV-crush trap veto
    if (f.get("vol_surge", 0) or 0) < CFG["vol_surge_min"]:
        # volume participation required (relaxed for S4 where wall IS the liquidity)
        return False
    return True


def s1_breakout(f, prev):
    """S1: OI-confirmed breakout."""
    if not _base_ok(f):
        return None
    cw, pw = f.get("call_wall"), f.get("put_wall")
    if not (cw and pw):
        return None

    # LONG CE setup: price above call wall, wall weakening, negative skew
    # (negative = net call buying / put unwinding at ATM)
    # trend alignment: don't buy calls into a falling 20-bar trend
    ret20 = f.get("ret_20") or 0
    long_ok = (cw and f["spot"] > cw.get("strike", 0) and cw.get("strong")
               and cw.get("weakening")
               and 0 < cw.get("dist", 0) < 0.03
               and f["atm_skew"] < -0.15
               and CFG["breakout_min_ret"] < (f.get("ret_5") or 0)
               < CFG["breakout_max_ret"]
               and (ret20 > -0.005))
    if long_ok:
        return {"type": "S1", "side": "BUY CE",
                "reason": (f"Breakout above call wall {cw['strike']:g} "
                           f"(OI {cw['oi']/1e6:.1f}M weakening), skew "
                           f"{f['atm_skew']:+.2f}, +{f['ret_5']*100:.1f}% in 5m"),
                "ref_strike": cw.get("strike"),
                "exit_ref": (pw or {}).get("strike")}

    # LONG PE mirror: spot below put wall, wall vacating (put writers
    # unwinding), negative skew confirms directional flow
    short_ok = (pw and f["spot"] < pw.get("strike", 1e9) and pw.get("strong")
                and pw.get("weakening")
                and -0.03 < pw.get("dist", 0) < 0
                and f["atm_skew"] < -0.15
                and -CFG["breakout_max_ret"]
                < (f.get("ret_5") or 0) < -CFG["breakout_min_ret"]
                and (ret20 < 0.005))
    if short_ok:
        return {"type": "S1", "side": "BUY PE",
                "reason": (f"Breakdown below put wall {pw['strike']:g} "
                           f"(OI {pw['oi']/1e6:.1f}M weakening), skew "
                           f"{f['atm_skew']:+.2f}, {f['ret_5']*100:.1f}% in 5m"),
                "ref_strike": pw.get("strike"),
                "exit_ref": (cw or {}).get("strike")}
    return None


def s2_squeeze(f, prev):
    """S2: short-covering squeeze — call writers above spot capitulating."""
    if not _base_ok(f):
        return None
    ret5 = f.get("ret_5") or 0
    if not (CFG["squeeze_min_ret"] < ret5 < CFG["squeeze_max_ret"]):
        return None  # not fast enough or already exhausted
    if f["atm_skew"] >= -0.15:  # need net call flow (negative skew)
        return None
    cw = f.get("call_wall")
    squeeze = False
    # dist = (spot - wall)/wall: negative when wall sits above spot
    if cw and -0.02 < cw.get("dist", 0) < 0:
        if cw.get("doi", 0) < CFG["squeeze_oi_drop"] * cw["oi"]:
            squeeze = True
    if not squeeze:
        return None
    return {"type": "S2", "side": "BUY CE",
            "reason": (f"Squeeze: call wall {cw['strike']:g} OI dropping "
                       f"{cw['doi']/cw['oi']*100:.0f}% while spot +{f['ret_5']*100:.1f}% "
                       f"in 5m, skew {f['atm_skew']:+.2f}"),
            "ref_strike": cw.get("strike"), "exit_ref": None}


def s3_pcr_reversal(f, prev):
    """S3: extreme PCR with skew flip — counter-trend reversal scalp."""
    if not _base_ok(f):
        return None
    m, sd = f.get("pcr_mean"), f.get("pcr_std")
    pcr = f.get("pcr_oi")
    if m is None or sd is None or sd < 0.05 or pcr is None:
        return None
    z = (pcr - m) / sd
    skew = f["atm_skew"]
    prev_skew = (prev or {}).get("atm_skew")

    long_ok = (z < -CFG["pcr_z_min"] and pcr < CFG["pcr_floor"]
               and skew < -0.15
               and (prev_skew is None or prev_skew > 0))
    if long_ok:
        return {"type": "S3", "side": "BUY CE",
                "reason": (f"PCR reversal: PCR {pcr:.2f} ({z:+.1f}σ low) with skew "
                           f"flipping negative (net call flow) "
                           f"{prev_skew:+.2f}->{skew:+.2f}"),
                "ref_strike": None, "exit_ref": None}

    short_ok = (z > CFG["pcr_z_min"] and pcr > CFG["pcr_ceil"]
                and skew > 0.15
                and (prev_skew is None or prev_skew < 0))
    if short_ok:
        return {"type": "S3", "side": "BUY PE",
                "reason": (f"PCR reversal: PCR {pcr:.2f} ({z:+.1f}σ high) with skew "
                           f"flipping positive (net put flow) "
                           f"{prev_skew:+.2f}->{skew:+.2f}"),
                "ref_strike": None, "exit_ref": None}
    return None


def s4_wall_fade(f, prev):
    """S4: wall defense fade — range scalp into a strengthening wall."""
    if not f.get("valid"):
        return None
    if f.get("iv_spike", 0) > CFG["iv_veto_spike"]:
        return None
    cw, pw = f.get("call_wall"), f.get("put_wall")

    # Fade up into call wall: spot near wall, wall strong & growing, skew negative
    # fade only against WEAK momentum (fading strong momentum = death)
    ret5 = f.get("ret_5") or 0
    # dist<0 when call wall is above spot (fade up into resistance)
    if cw and -CFG["wall_dist_max"] < cw.get("dist", 0) < 0 and cw.get("strong"):
        if (cw.get("doi", 0) > 0.05 * cw["oi"] and f["atm_skew"] > 0.15
                and -0.001 <= ret5 <= 0.003):
            return {"type": "S4", "side": "BUY PE",
                    "reason": (f"Fade into call wall {cw['strike']:g} "
                               f"(OI +{cw['doi']/cw['oi']*100:.0f}%, dist "
                               f"{cw['dist']*100:.2f}%), skew {f['atm_skew']:+.2f}"),
                    "ref_strike": cw.get("strike"), "exit_ref": f["max_put_strike"]}

    # Fade down into put wall: spot near wall, wall strong & growing, skew positive
    # dist>0 when put wall is below spot (fade down into support)
    if pw and 0 < pw.get("dist", 0) < CFG["wall_dist_max"] and pw.get("strong"):
        if (pw.get("doi", 0) > 0.05 * pw["oi"] and f["atm_skew"] < -0.15
                and -0.003 <= ret5 <= 0.001):
            return {"type": "S4", "side": "BUY CE",
                    "reason": (f"Fade into put wall {pw['strike']:g} "
                               f"(OI +{pw['doi']/pw['oi']*100:.0f}%, dist "
                               f"{abs(pw['dist'])*100:.2f}%), skew {f['atm_skew']:+.2f}"),
                    "ref_strike": pw.get("strike"), "exit_ref": f["max_call_strike"]}
    return None


def evaluate(f, prev, cooldown_by_stock: dict, symbol: str,
             cooldown_bars: int = 6) -> dict:
    """Run all signal types; respect per-stock cooldown."""
    last_fire = cooldown_by_stock.get(symbol, -999)
    bar_idx = f.get("_bar_idx", 0)
    if bar_idx - last_fire < cooldown_bars:
        return None
    for fn in (s1_breakout, s2_squeeze, s3_pcr_reversal, s4_wall_fade):
        sig = fn(f, prev)
        if sig:
            return sig
    return None

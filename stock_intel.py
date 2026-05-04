#!/usr/bin/env python3
"""
BullzStock Intelligence — v4.1
Fixes: sidebar prices, stock card click, TF compact buttons, chart stock bug,
       fundamentals display, visual metrics sizing, Pro UI, Screener crash,
       Telegram, ticker strip gap
"""

import math
import requests
import streamlit as st
from datetime import datetime
import os
import tempfile
import hashlib

os.environ["YFINANCE_CACHE_DIR"] = tempfile.gettempdir()

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="BullzStock Intelligence",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Config ────────────────────────────────────────────────────
AV_KEY   = ""
TG_TOKEN = ""
TG_CHAT  = ""

INDUSTRY_ICONS = {
    "IT": "💻", "Banking": "🏦", "FMCG": "🛒", "Fintech": "💳",
    "Automobile": "🚗", "Defence": "🛡️", "Retail/QSR": "🍕", "All": "📊",
}

STOCKS = {
    "PFOCUS":     {"name": "PI Focus",       "industry": "IT",         "yf": "PFOCUS.NS",     "av": "PFOCUS",     "fullName": "Photon Infotech Focus",   "tv": "NSE:PFOCUS"},
    "HDFCBANK":   {"name": "HDFC Bank",      "industry": "Banking",    "yf": "HDFCBANK.NS",   "av": "HDFCBANK",   "fullName": "HDFC Bank Ltd.",          "tv": "NSE:HDFCBANK"},
    "ITC":        {"name": "ITC Ltd.",        "industry": "FMCG",       "yf": "ITC.NS",        "av": "ITC",        "fullName": "ITC Limited",             "tv": "NSE:ITC"},
    "PNB":        {"name": "PNB",            "industry": "Banking",    "yf": "PNB.NS",        "av": "PNB",        "fullName": "Punjab National Bank",    "tv": "NSE:PNB"},
    "PAYTM":      {"name": "Paytm",          "industry": "Fintech",    "yf": "PAYTM.NS",      "av": "PAYTM",      "fullName": "One97 Communications",    "tv": "NSE:PAYTM"},
    "TATAMOTORS": {"name": "Tata Motors",    "industry": "Automobile", "yf": "TATAMOTORS.NS", "av": "TATAMOTORS", "fullName": "Tata Motors Ltd.",        "tv": "NSE:TATAMOTORS"},
    "HAL":        {"name": "HAL",            "industry": "Defence",    "yf": "HAL.NS",        "av": "HAL",        "fullName": "Hindustan Aeronautics",   "tv": "NSE:HAL"},
    "JUBLFOOD":   {"name": "Jubilant Foods", "industry": "Retail/QSR", "yf": "JUBLFOOD.NS",   "av": "JUBLFOOD",   "fullName": "Jubilant Foodworks Ltd.", "tv": "NSE:JUBLFOOD"},
}

TIMEFRAMES = {
    "1D": {"label": "1 Day",      "yf_period": "1d",  "yf_interval": "5m",  "av_func": "TIME_SERIES_INTRADAY", "av_interval": "60min", "tv_interval": "5"},
    "1W": {"label": "1 Week",     "yf_period": "5d",  "yf_interval": "1h",  "av_func": "TIME_SERIES_DAILY",    "av_interval": "",       "tv_interval": "60"},
    "1M": {"label": "1 Month",    "yf_period": "1mo", "yf_interval": "1d",  "av_func": "TIME_SERIES_DAILY",    "av_interval": "",       "tv_interval": "D"},
    "6M": {"label": "6 Months",   "yf_period": "6mo", "yf_interval": "1wk", "av_func": "TIME_SERIES_WEEKLY",   "av_interval": "",       "tv_interval": "W"},
    "9M": {"label": "6-9 Months", "yf_period": "9mo", "yf_interval": "1wk", "av_func": "TIME_SERIES_WEEKLY",   "av_interval": "",       "tv_interval": "W"},
}

SIGNAL_CONFIG = {
    "STRONG BUY":  {"color": "#1a7340", "bg": "#d4edda", "border": "#28a745", "icon": "▲▲",
                    "neon_color": "#BDFF00", "neon_bg": "rgba(189,255,0,0.06)", "neon_border": "rgba(189,255,0,0.25)",
                    "pro_color": "#00d084",  "pro_bg": "rgba(0,208,132,0.08)",  "pro_border": "rgba(0,208,132,0.3)"},
    "BUY":         {"color": "#155724", "bg": "#d4edda", "border": "#5cb85c", "icon": "▲",
                    "neon_color": "#BDFF00", "neon_bg": "rgba(189,255,0,0.06)", "neon_border": "rgba(189,255,0,0.25)",
                    "pro_color": "#00d084",  "pro_bg": "rgba(0,208,132,0.08)",  "pro_border": "rgba(0,208,132,0.3)"},
    "SHORT SELL":  {"color": "#721c24", "bg": "#f8d7da", "border": "#dc3545", "icon": "▼▼",
                    "neon_color": "#ff4d6a", "neon_bg": "rgba(255,77,106,0.08)", "neon_border": "rgba(255,77,106,0.25)",
                    "pro_color": "#ff4d6a",  "pro_bg": "rgba(255,77,106,0.08)",  "pro_border": "rgba(255,77,106,0.3)"},
    "SELL":        {"color": "#721c24", "bg": "#f8d7da", "border": "#e06c75", "icon": "▼",
                    "neon_color": "#ff4d6a", "neon_bg": "rgba(255,77,106,0.08)", "neon_border": "rgba(255,77,106,0.25)",
                    "pro_color": "#ff4d6a",  "pro_bg": "rgba(255,77,106,0.08)",  "pro_border": "rgba(255,77,106,0.3)"},
    "HOLD":        {"color": "#004085", "bg": "#cce5ff", "border": "#007bff", "icon": "▬",
                    "neon_color": "#4d9fff", "neon_bg": "rgba(77,159,255,0.08)", "neon_border": "rgba(77,159,255,0.25)",
                    "pro_color": "#4d9fff",  "pro_bg": "rgba(77,159,255,0.08)",  "pro_border": "rgba(77,159,255,0.3)"},
    "WAIT":        {"color": "#856404", "bg": "#fff3cd", "border": "#ffc107", "icon": "◌",
                    "neon_color": "#f5a623", "neon_bg": "rgba(245,166,35,0.08)", "neon_border": "rgba(245,166,35,0.25)",
                    "pro_color": "#f5a623",  "pro_bg": "rgba(245,166,35,0.08)",  "pro_border": "rgba(245,166,35,0.3)"},
}

# ── Session state defaults ────────────────────────────────────
_SS_DEFAULTS = {
    "signal_history": {},
    "chart_show_ema50": True,
    "chart_show_ema200": True,
    "chart_show_bb": True,
    "selected_ticker": "PFOCUS",
    "selected_tf": "1M",
    "ui_theme": "neon",
    "analyse_clicked": False,
    "sidebar_prices": {},
}
for k, v in _SS_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────
def fmt_inr(val):
    if val is None: return "—"
    return f"₹{float(val):,.2f}"

def fmt_pct(val):
    if val is None: return "—"
    sign = "+" if float(val) >= 0 else ""
    return f"{sign}{float(val):.2f}%"

def clean_list(lst):
    result = []
    for x in (lst or []):
        try:
            v = float(x)
            if not math.isnan(v):
                result.append(v)
        except (TypeError, ValueError):
            pass
    return result

def is_neon():
    return st.session_state.ui_theme == "neon"

def sig_color(sc):
    return sc["neon_color"] if is_neon() else sc["pro_color"]

def sig_bg(sc):
    return sc["neon_bg"] if is_neon() else sc["pro_bg"]

def sig_border(sc):
    return sc["neon_border"] if is_neon() else sc["pro_border"]

def badge_cls(reading):
    r = reading.lower()
    if any(x in r for x in ["bullish", "uptrend", "golden", "oversold", "above", "strong up"]): return "bz-badge-bull"
    if any(x in r for x in ["bearish", "downtrend", "death", "overbought", "below"]): return "bz-badge-bear"
    if any(x in r for x in ["warn", "near lower", "near upper", "moderate"]): return "bz-badge-warn"
    return "bz-badge-neut"

def acc_green():
    return "#BDFF00" if is_neon() else "#00d084"

def border_dim():
    return "rgba(255,255,255,0.06)" if is_neon() else "rgba(0,0,0,0.07)"

def bg_panel():
    return "rgba(255,255,255,0.03)" if is_neon() else "#ffffff"

def text_main():
    return "#e3e2e2" if is_neon() else "#1a2333"

def text_muted():
    return "#6b7a94"

# ══════════════════════════════════════════════════════════════
#  TECHNICAL INDICATORS
# ══════════════════════════════════════════════════════════════
def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return None
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        if d >= 0: gains += d
        else: losses += abs(d)
    avg_gain = gains / period
    avg_loss = losses / period
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i-1]
        avg_gain = (avg_gain * (period-1) + (d if d >= 0 else 0)) / period
        avg_loss = (avg_loss * (period-1) + (abs(d) if d < 0 else 0)) / period
    if avg_loss == 0: return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_ema(closes, period):
    if len(closes) < period: return None
    k = 2 / (period + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = price * k + ema * (1 - k)
    return ema

def calc_ema_series(closes, period):
    if len(closes) < period:
        return [None] * len(closes)
    k = 2 / (period + 1)
    result = [None] * (period - 1)
    ema = sum(closes[:period]) / period
    result.append(ema)
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
        result.append(ema)
    return result

def calc_bb_series(closes, period=20):
    upper_s, mid_s, lower_s = [], [], []
    for i in range(len(closes)):
        if i < period - 1:
            upper_s.append(None); mid_s.append(None); lower_s.append(None)
        else:
            sl  = closes[i - period + 1: i + 1]
            mid = sum(sl) / period
            std = math.sqrt(sum((v - mid)**2 for v in sl) / period)
            upper_s.append(mid + 2 * std)
            mid_s.append(mid)
            lower_s.append(mid - 2 * std)
    return upper_s, mid_s, lower_s

def calc_macd(closes):
    if len(closes) < 26:
        return {"macd": None, "signal": None, "hist": None, "trend": "N/A"}
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    macd_val = ema12 - ema26
    signal_line = macd_val * (2 / 10)
    hist = macd_val - signal_line
    return {"macd": macd_val, "signal": signal_line, "hist": hist,
            "trend": "Bullish" if hist > 0 else "Bearish"}

def calc_bollinger(closes, period=20):
    if len(closes) < period:
        return {"upper": None, "mid": None, "lower": None, "pct": None, "position": "N/A"}
    sl  = closes[-period:]
    mid = sum(sl) / period
    std = math.sqrt(sum((v - mid)**2 for v in sl) / period)
    upper = mid + 2 * std
    lower = mid - 2 * std
    last  = closes[-1]
    bpct  = ((last - lower) / (upper - lower) * 100) if (upper - lower) > 0 else 50
    position = "Near Upper (Overbought)" if bpct > 80 else "Near Lower (Oversold)" if bpct < 20 else "Mid Range"
    return {"upper": upper, "mid": mid, "lower": lower, "pct": bpct, "position": position}

def calc_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / period

def calc_stochastic(highs, lows, closes, k_period=14):
    if len(closes) < k_period: return None, None
    sl_high = max(highs[-k_period:])
    sl_low  = min(lows[-k_period:])
    if sl_high == sl_low: return 50.0, 50.0
    k = ((closes[-1] - sl_low) / (sl_high - sl_low)) * 100
    return k, k * 0.8

def detect_trend(closes):
    if len(closes) < 10: return "Insufficient data"
    mid   = len(closes) // 2
    slope = ((closes[-1] - closes[mid]) / closes[mid]) * 100
    if abs(slope) < 1.5:  return "Sideways (Range-bound)"
    if slope > 5:         return "Strong Uptrend"
    if slope > 1.5:       return "Mild Uptrend"
    if slope < -5:        return "Strong Downtrend"
    return "Mild Downtrend"

def detect_candlestick(opens, highs, lows, closes):
    if len(closes) < 3: return "Insufficient data"
    body       = abs(closes[-1] - opens[-1])
    rng        = highs[-1] - lows[-1]
    if rng == 0: return "No data"
    upper_wick = highs[-1] - max(closes[-1], opens[-1])
    lower_wick = min(closes[-1], opens[-1]) - lows[-1]
    if lower_wick > body * 2 and upper_wick < body * 0.3: return "Hammer (Bullish reversal)"
    if upper_wick > body * 2 and lower_wick < body * 0.3: return "Shooting Star (Bearish reversal)"
    if closes[-1] > closes[-2] > closes[-3] and closes[-1] > opens[-1]: return "Three White Soldiers (Strong Bullish)"
    if closes[-1] < closes[-2] < closes[-3] and closes[-1] < opens[-1]: return "Three Black Crows (Strong Bearish)"
    if body < rng * 0.1: return "Doji (Indecision)"
    if closes[-1] > closes[-2] and closes[-1] > opens[-1]: return "Bullish Engulfing"
    if closes[-1] < closes[-2] and closes[-1] < opens[-1]: return "Bearish Engulfing"
    return "No clear pattern"

def calc_volume_trend(volumes):
    if len(volumes) < 5: return "N/A"
    recent  = sum(volumes[-3:]) / 3
    earlier = sum(volumes[-6:-3]) / 3 if len(volumes) >= 6 else recent
    if earlier == 0: return "N/A"
    change = (recent - earlier) / earlier * 100
    if change > 20:  return f"Rising (+{change:.0f}%)"
    if change < -20: return f"Falling ({change:.0f}%)"
    return f"Stable ({change:+.0f}%)"

def compute_all(price_data):
    o = price_data["opens"];  h = price_data["highs"]
    l = price_data["lows"];   c = price_data["closes"]
    v = price_data["volumes"]
    sk, sd = calc_stochastic(h, l, c)
    return {
        "rsi":           calc_rsi(c),
        "macd":          calc_macd(c),
        "bollinger":     calc_bollinger(c),
        "ema50":         calc_ema(c, min(50,  len(c))),
        "ema200":        calc_ema(c, min(200, len(c))),
        "ema50_series":  calc_ema_series(c, min(50,  len(c))),
        "ema200_series": calc_ema_series(c, min(200, len(c))),
        "bb_series":     calc_bb_series(c),
        "atr":           calc_atr(h, l, c),
        "stoch_k":       sk,
        "stoch_d":       sd,
        "period_return": ((c[-1]-c[0])/c[0]*100) if len(c) >= 2 else None,
        "trend":         detect_trend(c),
        "pattern":       detect_candlestick(o, h, l, c),
        "volume_trend":  calc_volume_trend(v),
        "candles":       len(c),
    }

# ══════════════════════════════════════════════════════════════
#  SIGNAL ENGINE
# ══════════════════════════════════════════════════════════════
def generate_signal(closes, highs, lows, volumes, ind):
    rsi    = ind["rsi"];    macd   = ind["macd"]
    boll   = ind["bollinger"]; ema50  = ind["ema50"]
    ema200 = ind["ema200"];    atr    = ind["atr"]
    trend  = ind["trend"];     stoch_k = ind["stoch_k"]
    curr   = closes[-1]
    score  = 0; max_score = 0; votes = []

    max_score += 2
    if rsi is not None:
        if rsi < 30:   score += 2; votes.append(f"RSI {rsi:.1f} — Oversold (Strong Bullish)")
        elif rsi < 45: score += 1; votes.append(f"RSI {rsi:.1f} — Mildly Oversold (Bullish)")
        elif rsi > 70: score -= 2; votes.append(f"RSI {rsi:.1f} — Overbought (Strong Bearish)")
        elif rsi > 55: score -= 1; votes.append(f"RSI {rsi:.1f} — Mildly Overbought (Bearish)")
        else:          votes.append(f"RSI {rsi:.1f} — Neutral")

    max_score += 2
    if macd["hist"] is not None:
        if macd["hist"] > 0 and macd["macd"] > 0:
            score += 2; votes.append(f"MACD Bullish crossover (hist={macd['hist']:.3f})")
        elif macd["hist"] > 0:
            score += 1; votes.append("MACD Hist positive — mild bullish")
        elif macd["hist"] < 0 and macd["macd"] < 0:
            score -= 2; votes.append(f"MACD Bearish crossover (hist={macd['hist']:.3f})")
        else:
            score -= 1; votes.append("MACD Hist negative — mild bearish")

    max_score += 3
    if ema50 and ema200:
        if ema50 > ema200 and curr > ema50:
            score += 3; votes.append("Golden Cross + Price above EMA50 (Strong Bullish)")
        elif ema50 > ema200:
            score += 2; votes.append("Golden Cross (Bullish)")
        elif ema50 < ema200 and curr < ema50:
            score -= 3; votes.append("Death Cross + Price below EMA50 (Strong Bearish)")
        else:
            score -= 2; votes.append("Death Cross (Bearish)")
    elif ema50:
        if curr > ema50: score += 1; votes.append("Price above EMA50 (Bullish)")
        else:            score -= 1; votes.append("Price below EMA50 (Bearish)")

    max_score += 1
    if boll["pct"] is not None:
        if boll["pct"] < 20:   score += 1; votes.append(f"Bollinger %B={boll['pct']:.1f}% — Near lower band (Bullish)")
        elif boll["pct"] > 80: score -= 1; votes.append(f"Bollinger %B={boll['pct']:.1f}% — Near upper band (Bearish)")
        else:                  votes.append(f"Bollinger %B={boll['pct']:.1f}% — Mid range (Neutral)")

    max_score += 2
    if "Strong Uptrend"    in trend: score += 2; votes.append("Strong Uptrend confirmed")
    elif "Mild Uptrend"    in trend: score += 1; votes.append("Mild Uptrend")
    elif "Strong Downtrend" in trend: score -= 2; votes.append("Strong Downtrend confirmed")
    elif "Mild Downtrend"  in trend: score -= 1; votes.append("Mild Downtrend")
    else:                             votes.append("Sideways / Range-bound market")

    max_score += 1
    if stoch_k is not None:
        if stoch_k < 20:   score += 1; votes.append(f"Stochastic K={stoch_k:.1f} — Oversold (Bullish)")
        elif stoch_k > 80: score -= 1; votes.append(f"Stochastic K={stoch_k:.1f} — Overbought (Bearish)")

    max_score += 1
    vol_trend = ind["volume_trend"]
    if "Rising" in vol_trend and score > 0:  score += 1; votes.append("Rising volume confirms bullish move")
    elif "Rising" in vol_trend and score < 0: score -= 1; votes.append("Rising volume confirms bearish move")

    pct_bull = (score / max_score) * 100 if max_score > 0 else 0

    if pct_bull >= 60:       signal = "STRONG BUY"
    elif pct_bull >= 30:     signal = "BUY"
    elif pct_bull <= -60:    signal = "SHORT SELL"
    elif pct_bull <= -30:    signal = "SELL"
    elif abs(pct_bull) < 15: signal = "WAIT"
    else:                    signal = "HOLD"

    regime = ("Sideways/Ranging" if "Sideways" in trend or signal in ("HOLD","WAIT")
              else ("Trending Bullish" if "Strong" in trend else "Mild Bullish") if signal in ("STRONG BUY","BUY")
              else ("Trending Bearish" if "Strong" in trend else "Mild Bearish") if signal in ("SHORT SELL","SELL")
              else "Mixed/Volatile")

    if atr is None: atr = curr * 0.015
    atr_t = {"STRONG BUY": 3.0, "BUY": 2.0, "SHORT SELL": 3.0, "SELL": 2.0, "HOLD": 1.5, "WAIT": 1.0}
    atr_s = {"STRONG BUY": 1.5, "BUY": 1.2, "SHORT SELL": 1.5, "SELL": 1.2, "HOLD": 1.0, "WAIT": 0.8}

    is_short     = signal in ("SHORT SELL", "SELL")
    buy_price    = curr
    target_price = curr - atr * atr_t.get(signal, 2.0) if is_short else curr + atr * atr_t.get(signal, 2.0)
    stop_loss    = curr + atr * atr_s.get(signal, 1.2) if is_short else curr - atr * atr_s.get(signal, 1.2)

    profit_potential = abs((target_price - buy_price) / buy_price * 100)
    risk_amt         = abs(buy_price - stop_loss)
    reward_amt       = abs(target_price - buy_price)
    rr_ratio         = reward_amt / risk_amt if risk_amt > 0 else 0
    base_prob        = 40 + abs(pct_bull) * 0.4
    conf_bonus       = min(len([v for v in votes if "Strong" in v or "confirm" in v]) * 5, 20)
    success_prob     = min(max(base_prob + conf_bonus, 20), 90)

    duration_map = {
        "STRONG BUY": "2-4 weeks", "BUY": "3-6 weeks",
        "SHORT SELL": "1-3 weeks", "SELL": "Exit 1-2 weeks",
        "HOLD": "Review in 2 weeks", "WAIT": "Wait 1-5 days",
    }
    return {
        "signal": signal, "regime": regime, "score": score,
        "max_score": max_score, "pct_bull": pct_bull, "votes": votes,
        "buy_price": round(buy_price, 2), "target_price": round(target_price, 2),
        "stop_loss": round(stop_loss, 2), "profit_potential": round(profit_potential, 2),
        "rr_ratio": round(rr_ratio, 2), "success_prob": round(success_prob, 1),
        "hold_duration": duration_map.get(signal, "—"), "atr": round(atr, 2),
    }

def build_signal_reasoning(sig, ind, price_data):
    signal = sig["signal"]
    rsi    = ind["rsi"]
    trend  = ind["trend"]
    votes  = sig["votes"]
    bullish_reasons = [v for v in votes if "Bullish" in v or "Uptrend" in v]
    bearish_reasons = [v for v in votes if "Bearish" in v or "Downtrend" in v]
    if signal in ("STRONG BUY", "BUY"):
        top   = bullish_reasons[:2] if bullish_reasons else votes[:2]
        line1 = f"Signal driven by: {top[0].split('(')[0].strip()}" if top else "Multiple bullish indicators aligned."
        line2 = f"Also supported by: {top[1].split('(')[0].strip()}." if len(top) > 1 else f"Trend: {trend}."
    elif signal in ("SHORT SELL", "SELL"):
        top   = bearish_reasons[:2] if bearish_reasons else votes[:2]
        line1 = f"Signal driven by: {top[0].split('(')[0].strip()}" if top else "Multiple bearish indicators aligned."
        line2 = f"Also: {top[1].split('(')[0].strip()}." if len(top) > 1 else f"Trend: {trend}."
    elif signal == "HOLD":
        line1 = "Mixed signals — neither clearly bullish nor bearish."
        line2 = f"Price is ranging. RSI at {rsi:.0f} — neutral zone." if rsi else "Waiting for a clearer trend to emerge."
    else:
        line1 = "Insufficient directional conviction across indicators."
        line2 = "Consider waiting for RSI breakout or a MACD crossover before entering."
    return line1, line2

def get_news_link(ticker_symbol, full_name):
    encoded = full_name.replace(" ", "+")
    google_news  = f"https://news.google.com/search?q={encoded}+NSE+stock&hl=en-IN&gl=IN"
    moneycontrol = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data={ticker_symbol}&cid=&mbsearch_str=&type_search=News&news_op=&tagnews=y&sel_news=MNC"
    return google_news, moneycontrol

# ══════════════════════════════════════════════════════════════
#  DATA FETCHING
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def fetch_via_yfinance(yf_ticker, period, interval):
    try:
        url     = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_ticker}?range={period}&interval={interval}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r       = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data   = r.json()
            result = data.get("chart", {}).get("result", [None])[0]
            if result:
                meta       = result.get("meta", {})
                q          = result.get("indicators", {}).get("quote", [{}])[0]
                timestamps = result.get("timestamp", [])
                opens   = clean_list(q.get("open",   []))
                highs   = clean_list(q.get("high",   []))
                lows    = clean_list(q.get("low",    []))
                closes  = clean_list(q.get("close",  []))
                volumes = clean_list(q.get("volume", []))
                dates   = []
                for ts in timestamps:
                    try:    dates.append(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"))
                    except: dates.append("")
                if len(closes) >= 5:
                    curr = meta.get("regularMarketPrice") or closes[-1]
                    prev = meta.get("previousClose") or closes[-2]
                    return {
                        "source": "Yahoo Finance",
                        "current_price": curr, "prev_close": prev,
                        "open":   meta.get("regularMarketOpen",    opens[-1]   if opens   else curr),
                        "high":   meta.get("regularMarketDayHigh", highs[-1]   if highs   else curr),
                        "low":    meta.get("regularMarketDayLow",  lows[-1]    if lows    else curr),
                        "volume": meta.get("regularMarketVolume",  volumes[-1] if volumes else 0),
                        "change": curr - prev,
                        "change_pct": ((curr - prev) / prev * 100) if prev else 0,
                        "time": datetime.now().strftime("%H:%M"),
                        "opens": opens, "highs": highs, "lows": lows,
                        "closes": closes, "volumes": volumes,
                        "dates": dates if len(dates) == len(closes) else list(range(len(closes))),
                        "pe_ratio": None, "eps": None, "market_cap": None,
                        "revenue_growth": None, "debt_equity": None, "roe": None,
                        "dividend_yield": None,
                        "52w_high": meta.get("fiftyTwoWeekHigh"),
                        "52w_low":  meta.get("fiftyTwoWeekLow"),
                        "sector": None, "book_value": None, "price_to_book": None,
                        "current_ratio": None, "profit_margins": None,
                    }
    except Exception:
        pass

    if not YF_AVAILABLE: return None
    try:
        t    = yf.Ticker(yf_ticker)
        hist = t.history(period=period, interval=interval, auto_adjust=True)
        if hist.empty or len(hist) < 5: return None
        info = {}
        try: info = t.info
        except: pass
        opens   = clean_list(hist["Open"].tolist())
        highs   = clean_list(hist["High"].tolist())
        lows    = clean_list(hist["Low"].tolist())
        closes  = clean_list(hist["Close"].tolist())
        volumes = clean_list(hist["Volume"].tolist())
        dates   = [str(d)[:16] for d in hist.index.tolist()]
        curr    = closes[-1]; prev = closes[-2] if len(closes) >= 2 else curr

        def get_info(*keys):
            for k in keys:
                v = info.get(k)
                if v is not None: return v
            return None

        return {
            "source": "Yahoo Finance",
            "current_price": curr, "prev_close": prev,
            "open": opens[-1] if opens else curr,
            "high": highs[-1] if highs else curr,
            "low":  lows[-1]  if lows  else curr,
            "volume": volumes[-1] if volumes else 0,
            "change": curr - prev,
            "change_pct": ((curr - prev) / prev * 100) if prev else 0,
            "time": datetime.now().strftime("%H:%M"),
            "opens": opens, "highs": highs, "lows": lows,
            "closes": closes, "volumes": volumes, "dates": dates,
            "pe_ratio":       get_info("trailingPE", "forwardPE"),
            "eps":            get_info("trailingEps", "forwardEps"),
            "market_cap":     get_info("marketCap"),
            "revenue_growth": get_info("revenueGrowth", "earningsGrowth"),
            "debt_equity":    get_info("debtToEquity"),
            "roe":            get_info("returnOnEquity", "returnOnAssets"),
            "dividend_yield": get_info("dividendYield", "trailingAnnualDividendYield"),
            "52w_high":       get_info("fiftyTwoWeekHigh"),
            "52w_low":        get_info("fiftyTwoWeekLow"),
            "sector":         get_info("sector", "industry"),
            "book_value":     get_info("bookValue"),
            "price_to_book":  get_info("priceToBook"),
            "current_ratio":  get_info("currentRatio"),
            "profit_margins": get_info("profitMargins", "grossMargins"),
        }
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def fetch_quick_price(yf_ticker):
    """Lightweight single-stock price fetch for sidebar cards."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_ticker}?range=1d&interval=1d"
        r   = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if r.status_code == 200:
            meta = r.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice") or meta.get("chartPreviousClose")
            prev  = meta.get("previousClose") or meta.get("chartPreviousClose")
            if price and prev and prev > 0:
                pct = (price - prev) / prev * 100
                return {"price": price, "pct": pct}
    except Exception:
        pass
    return None

@st.cache_data(ttl=300)
def fetch_via_alphavantage(av_symbol, av_func, av_interval):
    url = f"https://www.alphavantage.co/query?function={av_func}&symbol={av_symbol}&apikey={AV_KEY}&outputsize=compact"
    if av_interval: url += f"&interval={av_interval}"
    try:
        r    = requests.get(url, timeout=15); r.raise_for_status()
        data = r.json()
        key  = next((k for k in data if "Time Series" in k), None)
        if not key: return None
        series = data[key]; dates = sorted(series.keys())
        opens, highs, lows, closes, volumes = [], [], [], [], []
        for d in dates:
            row = series[d]
            opens.append(float(row["1. open"]));   highs.append(float(row["2. high"]))
            lows.append(float(row["3. low"]));     closes.append(float(row["4. close"]))
            volumes.append(float(row.get("5. volume", 0)))
        curr = closes[-1]; prev = closes[-2] if len(closes) >= 2 else curr
        return {
            "source": "Alpha Vantage", "current_price": curr, "prev_close": prev,
            "open": opens[-1], "high": highs[-1], "low": lows[-1], "volume": volumes[-1],
            "change": curr - prev, "change_pct": ((curr-prev)/prev*100) if prev else 0,
            "time": datetime.now().strftime("%H:%M"),
            "opens": opens, "highs": highs, "lows": lows, "closes": closes,
            "volumes": volumes, "dates": dates,
            "pe_ratio": None, "eps": None, "market_cap": None, "revenue_growth": None,
            "debt_equity": None, "roe": None, "dividend_yield": None,
            "52w_high": None, "52w_low": None, "sector": None,
            "book_value": None, "price_to_book": None, "current_ratio": None, "profit_margins": None,
        }
    except Exception:
        return None

def fetch_market_data(ticker, tf_key):
    tf    = TIMEFRAMES[tf_key]
    stock = STOCKS[ticker]
    data  = fetch_via_yfinance(stock["yf"], tf["yf_period"], tf["yf_interval"])
    if not data:
        data = fetch_via_alphavantage(stock["av"], tf["av_func"], tf["av_interval"])
    return data

# ══════════════════════════════════════════════════════════════
#  TELEGRAM
# ══════════════════════════════════════════════════════════════
def send_telegram(message):
    """Send Telegram alert. Returns (success:bool, error:str)."""
    token = TG_TOKEN or st.secrets.get("TG_TOKEN", "")
    chat  = TG_CHAT  or st.secrets.get("TG_CHAT", "")
    if not token or not chat:
        return False, "TG_TOKEN or TG_CHAT not configured"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
        if r.status_code == 200:
            return True, ""
        return False, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, str(e)

# ══════════════════════════════════════════════════════════════
#  SIGNAL HISTORY
# ══════════════════════════════════════════════════════════════
def update_signal_history(ticker, rec):
    if ticker not in st.session_state.signal_history:
        st.session_state.signal_history[ticker] = []
    h = st.session_state.signal_history[ticker]
    if h and h[-1]["time"] == rec["time"]: h[-1] = rec
    else: h.append(rec)
    st.session_state.signal_history[ticker] = h[-10:]

# ══════════════════════════════════════════════════════════════
#  TRADINGVIEW CHART — bug fix: unique container_id per symbol+tf
# ══════════════════════════════════════════════════════════════
def render_tradingview_chart(tv_symbol, tv_interval, show_ema50, show_ema200, show_bb):
    studies = []
    if show_ema50:  studies.append('"MAExp@tv-basicstudies"')
    if show_ema200: studies.append('"MAExp@tv-basicstudies"')
    if show_bb:     studies.append('"BB@tv-basicstudies"')
    studies_str = "[" + ",".join(studies) + "]"

    # Unique container ID prevents TradingView iframe caching wrong stock
    uid   = hashlib.md5(f"{tv_symbol}{tv_interval}".encode()).hexdigest()[:8]
    cid   = f"tv_{uid}"
    theme = "dark" if is_neon() else "light"

    widget_html = f"""
    <div class="tradingview-widget-container" style="height:490px;width:100%">
      <div id="{cid}" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      (function(){{
        if(typeof TradingView === 'undefined') return;
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{tv_symbol}",
          "interval": "{tv_interval}",
          "timezone": "Asia/Kolkata",
          "theme": "{theme}",
          "style": "1",
          "locale": "en",
          "enable_publishing": false,
          "withdateranges": true,
          "hide_side_toolbar": false,
          "allow_symbol_change": false,
          "save_image": false,
          "studies": {studies_str},
          "container_id": "{cid}",
          "hide_top_toolbar": false,
          "show_popup_button": true,
          "popup_width": "1000",
          "popup_height": "650"
        }});
      }})();
      </script>
    </div>"""
    st.components.v1.html(widget_html, height=500, scrolling=False)

# ══════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ══════════════════════════════════════════════════════════════
def inject_global_css():
    common = """
    /* Remove Streamlit default padding top */
    .main .block-container { padding-top: 1rem !important; }
    /* Hide default Streamlit footer */
    footer { display: none !important; }
    """

    if is_neon():
        theme_css = """
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background: #0a0b0d !important; color: #e3e2e2 !important;
            font-family: 'Manrope', sans-serif !important;
        }
        [data-testid="stSidebar"] { background: #060709 !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
        [data-testid="stSidebar"] * { color: #c9d1d9 !important; font-family: 'Manrope', sans-serif !important; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #e3e2e2 !important; }
        [data-testid="stMain"], [data-testid="stMainBlockContainer"] { background: #0a0b0d !important; }

        /* Sidebar selectbox */
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
            background: #111315 !important; border: 1px solid rgba(255,255,255,0.08) !important;
            color: #e3e2e2 !important; border-radius: 6px !important;
        }

        /* All buttons - base */
        .stButton > button {
            font-family: 'Manrope', sans-serif !important; font-weight: 700 !important;
            border-radius: 6px !important; transition: all 0.15s !important;
            font-size: 11px !important;
        }
        /* Primary = Analyse Now */
        .stButton > button[kind="primary"] {
            background: #8aad00 !important;
            color: #0a1000 !important;
            border: none !important;
            font-size: 12px !important;
            font-weight: 900 !important;
            letter-spacing: 0.05em !important;
        }
        .stButton > button[kind="primary"]:hover {
            background: #a3cc00 !important;
        }
        /* Secondary buttons */
        .stButton > button[kind="secondary"] {
            background: #111315 !important;
            color: #8b949e !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
        }
        .stButton > button[kind="secondary"]:hover {
            color: #c9d1d9 !important;
            border-color: rgba(255,255,255,0.15) !important;
        }

        h1,h2,h3,h4,h5 { color: #e3e2e2 !important; font-family: 'Manrope', sans-serif !important; }

        /* Ticker strip marquee */
        @keyframes bz-marquee { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }

        /* Sidebar stock card styles */
        .bz-sb-card {
            background: #111315; border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px; padding: 9px 12px; margin: 3px 0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .bz-sb-card.active {
            border-color: rgba(189,255,0,0.4);
            background: rgba(189,255,0,0.03);
            border-left: 3px solid #BDFF00;
        }
        .bz-sb-tk  { font-size: 12px; font-weight: 800; color: #e3e2e2; display:block; }
        .bz-sb-nm  { font-size: 9px;  color: #6b7a94; display:block; margin-top: 1px; }
        .bz-sb-pr  { font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600; text-align: right; display:block; }
        .bz-sb-pos { color: #BDFF00; }
        .bz-sb-neg { color: #ff4d6a; }

        /* OHLCV */
        .bz-ohlcv { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px 12px; text-align: center; }
        .bz-ohlcv-label { font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 5px; }
        .bz-ohlcv-val { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; color: #e3e2e2; }

        /* Signal box */
        .bz-signal-box { border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
        .bz-trade-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-bottom: 10px; }
        .bz-trade-cell { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 9px 11px; }
        .bz-trade-label { font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 3px; }
        .bz-trade-val { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; }
        .bz-trade-sub { font-size: 10px; margin-top: 2px; color: #6b7a94; }

        /* Votes */
        .bz-vote-row { display: flex; align-items: flex-start; gap: 7px; font-size: 10px; color: #8b949e; padding: 2px 0; line-height: 1.4; }
        .bz-vote-icon { width: 13px; height: 13px; min-width: 13px; border-radius: 3px; display: inline-flex; align-items: center; justify-content: center; font-size: 8px; margin-top: 1px; }

        /* Indicator rows */
        .bz-ind-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 11px; }
        .bz-ind-row:last-child { border-bottom: none; }
        .bz-ind-key { color: #6b7a94; }
        .bz-ind-badge { font-size: 9px; padding: 2px 5px; border-radius: 3px; margin-left: 5px; font-weight: 600; white-space: nowrap; }
        .bz-badge-bull { background: rgba(189,255,0,0.1);   color: #BDFF00; }
        .bz-badge-bear { background: rgba(255,77,106,0.1);  color: #ff4d6a; }
        .bz-badge-neut { background: rgba(255,255,255,0.06); color: #8b949e; }
        .bz-badge-warn { background: rgba(245,166,35,0.1);  color: #f5a623; }

        /* History table */
        .bz-hist-table { width: 100%; border-collapse: collapse; font-size: 11px; }
        .bz-hist-table th { text-align: left; padding: 4px 8px; font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .bz-hist-table td { padding: 6px 8px; border-top: 1px solid rgba(255,255,255,0.04); font-family: 'IBM Plex Mono', monospace; }
        .bz-hist-table tr:hover td { background: rgba(255,255,255,0.02); }

        /* Metric gauge cards — equal height */
        .bz-metric-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 8px 10px; text-align: center; height: 150px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; }
        .bz-metric-label { font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px; }
        .bz-metric-val { font-family: 'IBM Plex Mono', monospace; font-size: 18px; font-weight: 700; }
        .bz-metric-sub { font-size: 10px; color: #6b7a94; }

        /* Panel title */
        .bz-panel-title { font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.16em; color: #6b7a94; margin-bottom: 10px; padding-bottom: 7px; border-bottom: 1px solid rgba(255,255,255,0.06); }

        /* Price header */
        .bz-price-header { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; }

        /* Disclaimer */
        .bz-disclaimer { font-size: 10px; color: #6b7a94; padding: 10px 14px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; line-height: 1.6; margin-top: 14px; }

        /* Ticker strip */
        .bz-ticker-strip { background: #060709; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 7px 0; overflow: hidden; white-space: nowrap; margin-bottom: 14px; }
        .bz-ticker-inner { display: inline-flex; gap: 2rem; animation: bz-marquee 30s linear infinite; padding-left: 1rem; }
        .bz-ticker-item { font-size: 10px; font-weight: 700; font-family: 'IBM Plex Mono', monospace; color: #8b949e; }
        .bz-tk  { color: #c9d1d9; }
        .bz-pos { color: #BDFF00; }
        .bz-neg { color: #ff4d6a; }
        """
    else:
        theme_css = """
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background: #f0f4f8 !important; color: #1a2333 !important;
            font-family: 'Syne', sans-serif !important;
        }
        [data-testid="stSidebar"] { background: #0d1219 !important; border-right: 1px solid rgba(255,255,255,0.07) !important; }
        [data-testid="stSidebar"] * { color: #e8edf5 !important; font-family: 'Syne', sans-serif !important; }
        [data-testid="stMain"], [data-testid="stMainBlockContainer"] { background: #f0f4f8 !important; }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
            background: #111820 !important; border: 1px solid rgba(255,255,255,0.1) !important;
            color: #e8edf5 !important; border-radius: 6px !important;
        }

        .stButton > button { font-family: 'Syne', sans-serif !important; font-weight: 700 !important; border-radius: 6px !important; font-size: 11px !important; }
        .stButton > button[kind="primary"] { background: #00a86b !important; color: #fff !important; border: none !important; font-size: 12px !important; font-weight: 900 !important; }
        .stButton > button[kind="primary"]:hover { background: #00c27a !important; }
        .stButton > button[kind="secondary"] { background: #111820 !important; color: #6b7a94 !important; border: 1px solid rgba(255,255,255,0.1) !important; }

        h1,h2,h3,h4,h5 { color: #1a2333 !important; font-family: 'Syne', sans-serif !important; }

        @keyframes bz-marquee { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }

        .bz-sb-card { background: #111820; border: 1px solid rgba(255,255,255,0.07); border-radius: 8px; padding: 9px 12px; margin: 3px 0; display: flex; justify-content: space-between; align-items: center; }
        .bz-sb-card.active { border-color: rgba(0,208,132,0.4); background: rgba(0,208,132,0.05); border-left: 3px solid #00d084; }
        .bz-sb-tk  { font-size: 12px; font-weight: 800; color: #e8edf5; display: block; }
        .bz-sb-nm  { font-size: 9px; color: #6b7a94; display: block; margin-top: 1px; }
        .bz-sb-pr  { font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600; text-align: right; display: block; }
        .bz-sb-pos { color: #00d084; }
        .bz-sb-neg { color: #ff4d6a; }

        .bz-ohlcv { background: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 10px 12px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .bz-ohlcv-label { font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 5px; }
        .bz-ohlcv-val { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; color: #1a2333; }

        .bz-signal-box { border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
        .bz-trade-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-bottom: 10px; }
        .bz-trade-cell { background: #f8fafc; border: 1px solid rgba(0,0,0,0.07); border-radius: 8px; padding: 9px 11px; }
        .bz-trade-label { font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 3px; }
        .bz-trade-val { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; color: #1a2333; }
        .bz-trade-sub { font-size: 10px; margin-top: 2px; color: #6b7a94; }

        .bz-vote-row { display: flex; align-items: flex-start; gap: 7px; font-size: 10px; color: #6b7a94; padding: 2px 0; line-height: 1.4; }
        .bz-vote-icon { width: 13px; height: 13px; min-width: 13px; border-radius: 3px; display: inline-flex; align-items: center; justify-content: center; font-size: 8px; margin-top: 1px; }

        .bz-ind-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid rgba(0,0,0,0.06); font-size: 11px; }
        .bz-ind-row:last-child { border-bottom: none; }
        .bz-ind-key { color: #6b7a94; }
        .bz-ind-badge { font-size: 9px; padding: 2px 5px; border-radius: 3px; margin-left: 5px; font-weight: 600; white-space: nowrap; }
        .bz-badge-bull { background: rgba(0,208,132,0.1);  color: #00a86b; }
        .bz-badge-bear { background: rgba(255,77,106,0.1); color: #ff4d6a; }
        .bz-badge-neut { background: rgba(0,0,0,0.06);     color: #6b7a94; }
        .bz-badge-warn { background: rgba(245,166,35,0.1); color: #c47d00; }

        .bz-hist-table { width: 100%; border-collapse: collapse; font-size: 11px; }
        .bz-hist-table th { text-align: left; padding: 4px 8px; font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; border-bottom: 1px solid rgba(0,0,0,0.08); }
        .bz-hist-table td { padding: 6px 8px; border-top: 1px solid rgba(0,0,0,0.05); font-family: 'IBM Plex Mono', monospace; color: #1a2333; }
        .bz-hist-table tr:hover td { background: rgba(0,0,0,0.02); }

        .bz-metric-card { background: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; padding: 12px 8px 10px; text-align: center; height: 150px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
        .bz-metric-label { font-size: 9px; color: #6b7a94; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px; }
        .bz-metric-val { font-family: 'IBM Plex Mono', monospace; font-size: 18px; font-weight: 700; }
        .bz-metric-sub { font-size: 10px; color: #6b7a94; }

        .bz-panel-title { font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.16em; color: #6b7a94; margin-bottom: 10px; padding-bottom: 7px; border-bottom: 1px solid rgba(0,0,0,0.08); }
        .bz-price-header { background: #ffffff; border: 1px solid rgba(0,0,0,0.07); border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .bz-disclaimer { font-size: 10px; color: #6b7a94; padding: 10px 14px; background: #ffffff; border: 1px solid rgba(0,0,0,0.07); border-radius: 8px; line-height: 1.6; margin-top: 14px; }

        .bz-ticker-strip { background: #0d1219; border-radius: 8px; padding: 7px 0; overflow: hidden; white-space: nowrap; margin-bottom: 14px; }
        .bz-ticker-inner { display: inline-flex; gap: 2rem; animation: bz-marquee 30s linear infinite; padding-left: 1rem; }
        .bz-ticker-item { font-size: 10px; font-weight: 700; font-family: 'IBM Plex Mono', monospace; color: #6b7a94; }
        .bz-tk  { color: #e8edf5; }
        .bz-pos { color: #00d084; }
        .bz-neg { color: #ff4d6a; }
        """

    st.markdown(f"<style>{common}{theme_css}</style>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TICKER STRIP
# ══════════════════════════════════════════════════════════════
def render_ticker_strip():
    items = [
        ("NIFTY 50", "22,456", "+0.84%", True),
        ("SENSEX",   "73,852", "+0.76%", True),
        ("BANKNIFTY","48,210", "−0.22%", False),
        ("BAJAJ-AUTO","9,994", "+4.60%", True),
        ("RELIANCE",  "1,430", "+6.50%", True),
        ("HDFCBANK",  "1,680", "+2.10%", True),
        ("PFOCUS",    "308.15","−1.96%", False),
        ("ITC",       "450.20","+1.22%", True),
        ("TATAMOTORS","910.55","−0.35%", False),
        ("HAL",      "4,250", "+1.80%", True),
    ]
    def item_html(tkr, price, pct, up):
        cls = "bz-pos" if up else "bz-neg"
        return f'<span class="bz-ticker-item"><span class="bz-tk">{tkr}</span> <span class="{cls}">{price} {pct}</span></span>'

    inner = "".join(item_html(*i) for i in items)
    # Duplicate for seamless loop
    st.markdown(f"""
    <div class="bz-ticker-strip">
      <div class="bz-ticker-inner">
        <div style="display:inline-flex;gap:2.5rem;padding-right:2.5rem">{inner}</div>
        <div style="display:inline-flex;gap:2.5rem;padding-right:2.5rem">{inner}</div>
      </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        ag = acc_green()

        # ── Logo ─────────────────────────────────────────────
        logo_bg = "#8aad00" if is_neon() else "#00d084"
        st.markdown(f"""
        <div style="padding:14px 8px 12px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:32px;height:32px;background:{logo_bg};border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px">🐂</div>
            <div>
              <div style="font-size:14px;font-weight:800;color:{ag};letter-spacing:0.01em">BullzStock</div>
              <div style="font-size:8px;color:#6b7a94;letter-spacing:0.15em;text-transform:uppercase;margin-top:1px">NSE India · Signal Engine</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Theme toggle ─────────────────────────────────────
        st.markdown('<div style="font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:#6b7a94;margin-bottom:5px">UI Theme</div>', unsafe_allow_html=True)
        tc1, tc2 = st.columns(2)
        with tc1:
            neon_type = "primary" if is_neon() else "secondary"
            if st.button("⚡ Neon", key="btn_neon", use_container_width=True, type=neon_type):
                st.session_state.ui_theme = "neon"; st.rerun()
        with tc2:
            pro_type = "primary" if not is_neon() else "secondary"
            if st.button("🔷 Pro", key="btn_pro", use_container_width=True, type=pro_type):
                st.session_state.ui_theme = "pro"; st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:10px 0'>", unsafe_allow_html=True)

        # ── Industry filter ───────────────────────────────────
        industries = ["All"] + sorted(set(v["industry"] for v in STOCKS.values()))
        chosen_ind = st.selectbox(
            "🏭 Industry",
            industries,
            format_func=lambda x: f"{INDUSTRY_ICONS.get(x,'📌')} {x}",
            label_visibility="collapsed"
        )
        filtered = {k: v for k, v in STOCKS.items() if chosen_ind == "All" or v["industry"] == chosen_ind}

        # ── Stock cards with live prices ──────────────────────
        st.markdown('<div style="font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:#6b7a94;margin:8px 0 5px">Select Stock</div>', unsafe_allow_html=True)

        for tkr, info in filtered.items():
            is_active = st.session_state.selected_ticker == tkr
            active_cls = "active" if is_active else ""

            # Fetch quick price for this ticker (cached 60s)
            qp = fetch_quick_price(info["yf"])
            if qp:
                price_str = f"₹{qp['price']:,.1f}"
                pct_val   = qp["pct"]
                pct_str   = f"{'+' if pct_val >= 0 else ''}{pct_val:.2f}%"
                pct_cls   = "bz-sb-pos" if pct_val >= 0 else "bz-sb-neg"
            else:
                price_str = "—"
                pct_str   = "NSE"
                pct_cls   = "bz-sb-pos" if is_neon() else "bz-sb-pos"

            # Render card HTML + invisible button overlay
            st.markdown(f"""
            <div class="bz-sb-card {active_cls}">
              <div>
                <span class="bz-sb-tk">{tkr}</span>
                <span class="bz-sb-nm">{info['name']}</span>
              </div>
              <div>
                <span class="bz-sb-pr {pct_cls}">{price_str}</span>
                <span class="bz-sb-pr {pct_cls}" style="font-size:9px">{pct_str}</span>
              </div>
            </div>""", unsafe_allow_html=True)

            # Slim transparent button below card — acts as click target
            if st.button(f"Select {tkr}", key=f"pick_{tkr}", use_container_width=True,
                         help=f"Analyse {tkr}"):
                st.session_state.selected_ticker = tkr
                st.session_state.analyse_clicked  = False
                st.rerun()

        # ── Timeframe — compact inline pills ─────────────────
        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:10px 0'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:#6b7a94;margin-bottom:6px">Timeframe</div>', unsafe_allow_html=True)

        tf_keys = list(TIMEFRAMES.keys())
        tf_cols = st.columns(len(tf_keys))
        for i, tf_key in enumerate(tf_keys):
            with tf_cols[i]:
                is_tf = st.session_state.selected_tf == tf_key
                btn_type = "primary" if is_tf else "secondary"
                if st.button(tf_key, key=f"tf_{tf_key}", use_container_width=True, type=btn_type):
                    st.session_state.selected_tf = tf_key
                    st.rerun()

        # ── Analyse Now ───────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡  Analyse Now", use_container_width=True, type="primary", key="analyse_btn"):
            st.session_state.analyse_clicked = True
            st.rerun()

        # ── Selected stock info ───────────────────────────────
        s = STOCKS[st.session_state.selected_ticker]
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                    border-radius:8px;padding:10px 12px;margin-top:8px">
          <div style="font-size:11px;font-weight:800;color:{ag}">{INDUSTRY_ICONS.get(s['industry'],'📌')} {st.session_state.selected_ticker}</div>
          <div style="font-size:10px;margin-top:2px;color:#c9d1d9">{s['fullName']}</div>
          <div style="font-size:9px;color:#6b7a94;margin-top:5px">{s['industry']} · {TIMEFRAMES[st.session_state.selected_tf]['label']}</div>
        </div>""", unsafe_allow_html=True)

        # ── Footer ────────────────────────────────────────────
        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:12px 0 6px'>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:9px;color:#6b7a94;line-height:1.8;padding:0 2px">
          NSE · Mon–Fri 9:15–15:30 IST · Yahoo Finance
        </div>""", unsafe_allow_html=True)

        if st.button("🗑 Clear History", use_container_width=True, key="clear_hist"):
            st.session_state.signal_history = {}
            st.success("Cleared")

# ══════════════════════════════════════════════════════════════
#  OHLCV BAR
# ══════════════════════════════════════════════════════════════
def render_ohlcv(price_data):
    ag = acc_green()
    cols = st.columns(6)
    cells = [
        ("Open",     fmt_inr(price_data["open"]),             None),
        ("High",     fmt_inr(price_data["high"]),             ag),
        ("Low",      fmt_inr(price_data["low"]),              "#ff4d6a"),
        ("Volume",   f"{price_data['volume']/1e5:.1f}L",      None),
        ("52W High", fmt_inr(price_data.get("52w_high")),     ag),
        ("52W Low",  fmt_inr(price_data.get("52w_low")),      "#ff4d6a"),
    ]
    for i, (label, val, color) in enumerate(cells):
        c = f"color:{color};" if color else ""
        with cols[i]:
            st.markdown(
                f'<div class="bz-ohlcv"><div class="bz-ohlcv-label">{label}</div>'
                f'<div class="bz-ohlcv-val" style="{c}">{val}</div></div>',
                unsafe_allow_html=True
            )

# ══════════════════════════════════════════════════════════════
#  INDICATOR ROW HELPER  (module-level — fixes fundamentals bug)
# ══════════════════════════════════════════════════════════════
def ind_row_html(label, val, badge_text="", badge_class=""):
    badge = f'<span class="bz-ind-badge {badge_class}">{badge_text}</span>' if badge_text else ""
    return (f'<div class="bz-ind-row">'
            f'<span class="bz-ind-key">{label}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:11px">{val}{badge}</span>'
            f'</div>')

# ══════════════════════════════════════════════════════════════
#  VISUAL METRICS — equal-height gauge cards
# ══════════════════════════════════════════════════════════════
def render_visual_metrics(rsi_val, prob_val, rr_ratio, closes, period_return):
    ag    = acc_green()
    track = "#1e2022" if is_neon() else "#e8eef4"

    rsi_color  = "#ff4d6a" if (rsi_val or 50) > 70 else ag if (rsi_val or 50) < 30 else "#f5a623"
    rsi_label  = "Overbought" if (rsi_val or 50) > 70 else "Oversold" if (rsi_val or 50) < 30 else "Neutral"
    rsi_disp   = f"{rsi_val:.1f}" if rsi_val else "—"
    prob_color = ag if prob_val >= 65 else "#f5a623" if prob_val >= 45 else "#ff4d6a"
    rr_color   = ag if rr_ratio >= 2 else "#f5a623" if rr_ratio >= 1 else "#ff4d6a"
    pr_color   = ag if (period_return or 0) >= 0 else "#ff4d6a"
    pr_text    = fmt_pct(period_return) if period_return is not None else "—"
    txt        = "#e3e2e2" if is_neon() else "#1a2333"

    # Semi-circle gauge SVG — fixed viewBox so all cards equal height
    def gauge_svg(val, max_val, color, disp, sub):
        pct   = min(max(val / max_val, 0.0), 1.0)
        angle = pct * 180 - 180
        rad   = math.radians(angle)
        nx    = 50 + 35 * math.cos(rad)
        ny    = 46 + 35 * math.sin(rad)
        ex    = 50 + 43 * math.cos(math.radians(pct * 180 - 180))
        ey    = 46 + 43 * math.sin(math.radians(pct * 180 - 180))
        large = 1 if pct > 0.5 else 0
        return f"""<div class="bz-metric-card">
          <div class="bz-metric-label">{sub}</div>
          <svg viewBox="0 0 100 50" xmlns="http://www.w3.org/2000/svg" style="width:90px;height:50px">
            <path d="M8 46 A42 42 0 0 1 92 46" fill="none" stroke="{track}" stroke-width="8" stroke-linecap="round"/>
            <path d="M8 46 A42 42 0 {large} 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
            <line x1="50" y1="46" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <circle cx="50" cy="46" r="3" fill="{color}"/>
          </svg>
          <div class="bz-metric-val" style="color:{color}">{disp}</div>
          <div class="bz-metric-sub">{rsi_label if 'RSI' in sub else ('High' if prob_val>=65 else 'Moderate' if prob_val>=45 else 'Low') if 'Prob' in sub else ''}</div>
        </div>"""

    rsi_html  = gauge_svg(rsi_val or 50, 100, rsi_color, rsi_disp, "RSI (14)")
    prob_html = gauge_svg(prob_val, 100, prob_color, f"{prob_val:.0f}%", "Success Prob")

    # R:R donut
    total = 1 + max(rr_ratio, 0.01)
    circ  = 2 * math.pi * 24
    rd    = (1 / total) * circ
    rwd   = (max(rr_ratio, 0.01) / total) * circ
    rr_html = f"""<div class="bz-metric-card">
      <div class="bz-metric-label">Risk : Reward</div>
      <svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg" style="width:58px;height:58px">
        <circle cx="30" cy="30" r="24" fill="none" stroke="#ff4d6a" stroke-width="8"
                stroke-dasharray="{rd:.1f} {circ:.1f}" stroke-dashoffset="0" transform="rotate(-90 30 30)"/>
        <circle cx="30" cy="30" r="24" fill="none" stroke="{ag}" stroke-width="8"
                stroke-dasharray="{rwd:.1f} {circ:.1f}" stroke-dashoffset="{-rd:.1f}" transform="rotate(-90 30 30)"/>
        <text x="30" y="27" text-anchor="middle" font-family="IBM Plex Mono" font-size="6.5" fill="{txt}" font-weight="700">1:{rr_ratio:.1f}</text>
        <text x="30" y="36" text-anchor="middle" font-family="IBM Plex Mono" font-size="5.5" fill="#6b7a94">R:R</text>
      </svg>
      <div class="bz-metric-val" style="color:{rr_color};font-size:15px">1:{rr_ratio:.2f}</div>
      <div class="bz-metric-sub">{'Good ≥2x' if rr_ratio >= 2 else 'Fair 1–2x' if rr_ratio >= 1 else 'Poor <1x'}</div>
    </div>"""

    # Sparkline
    spark = ""
    if closes and len(closes) > 1:
        mn, mx = min(closes), max(closes)
        rng = mx - mn if mx != mn else 1
        pts = [f"{int(i/(len(closes)-1)*80)},{int(36-((c-mn)/rng)*34)}" for i, c in enumerate(closes)]
        spark = f'<polyline points="{" ".join(pts)}" fill="none" stroke="{pr_color}" stroke-width="1.8" stroke-linejoin="round"/>'

    spark_html = f"""<div class="bz-metric-card">
      <div class="bz-metric-label">Period Return</div>
      <svg viewBox="0 0 80 38" xmlns="http://www.w3.org/2000/svg" style="width:80px;height:38px">{spark}</svg>
      <div class="bz-metric-val" style="color:{pr_color}">{pr_text}</div>
      <div class="bz-metric-sub">{'Positive' if (period_return or 0) >= 0 else 'Negative'}</div>
    </div>"""

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(rsi_html,  unsafe_allow_html=True)
    with c2: st.markdown(prob_html, unsafe_allow_html=True)
    with c3: st.markdown(rr_html,   unsafe_allow_html=True)
    with c4: st.markdown(spark_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  RIGHT PANEL
# ══════════════════════════════════════════════════════════════
def render_right_panel(sig, ind, price_data, stock, tf, ticker):
    sc       = SIGNAL_CONFIG.get(sig["signal"], SIGNAL_CONFIG["WAIT"])
    signal   = sig["signal"]
    curr     = price_data["current_price"]
    ag       = acc_green()
    sc_color = sig_color(sc)
    sc_bg_   = sig_bg(sc)
    sc_bdr   = sig_border(sc)
    line1, line2 = build_signal_reasoning(sig, ind, price_data)

    # Intensity bar
    score_norm = (sig["pct_bull"] + 100) / 200
    segs = []
    for thresh in [0.25, 0.4, 0.6, 0.75, 1.0]:
        if score_norm >= thresh:
            c = ag if score_norm > 0.6 else "#f5a623" if score_norm > 0.4 else "#ff4d6a"
        else:
            c = "rgba(255,255,255,0.08)" if is_neon() else "rgba(0,0,0,0.08)"
        segs.append(f'<div style="height:5px;flex:1;background:{c};border-radius:3px"></div>')

    confluence = f"{abs(sig['pct_bull']):.0f}% {'bullish' if sig['pct_bull'] >= 0 else 'bearish'}"

    votes_html = ""
    for v in sig["votes"][:6]:
        is_bull = any(x in v for x in ["Bullish", "Uptrend", "Golden", "confirm", "above"])
        icon_bg = f"rgba({'189,255,0' if is_neon() else '0,208,132'},0.1)" if is_bull else "rgba(255,77,106,0.1)"
        icon_c  = ag if is_bull else "#ff4d6a"
        arrow   = "▲" if is_bull else "▼"
        votes_html += f'<div class="bz-vote-row"><div class="bz-vote-icon" style="background:{icon_bg};color:{icon_c}">{arrow}</div><span>{v}</span></div>'

    bd = border_dim()
    reasoning_bg = "rgba(255,255,255,0.03)" if is_neon() else "#f8fafc"

    st.markdown(f'<div class="bz-panel-title">Signal Analysis</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="bz-signal-box" style="background:{sc_bg_};border:1px solid {sc_bdr}">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
        <div>
          <div style="font-size:8px;color:{sc_color};text-transform:uppercase;letter-spacing:0.12em;font-weight:700;margin-bottom:3px">Signal · {tf['label']}</div>
          <div style="font-size:20px;font-weight:900;color:{sc_color}">{sc['icon']} {signal}</div>
        </div>
        <div style="font-size:9px;font-weight:700;padding:4px 10px;border-radius:20px;background:{sc_bg_};color:{sc_color};border:1px solid {sc_bdr}">{confluence}</div>
      </div>
      <div style="font-size:10px;color:#8b949e;padding-top:7px;border-top:1px solid {bd}">Regime: <span style="color:{sc_color};font-weight:600">{sig['regime']}</span></div>
    </div>

    <div class="bz-trade-grid">
      <div class="bz-trade-cell">
        <div class="bz-trade-label">Entry</div>
        <div class="bz-trade-val" style="color:{'#4d9fff' if is_neon() else '#2563eb'}">{fmt_inr(sig['buy_price'])}</div>
        <div class="bz-trade-sub">Buy zone</div>
      </div>
      <div class="bz-trade-cell">
        <div class="bz-trade-label">Target</div>
        <div class="bz-trade-val" style="color:{ag}">{fmt_inr(sig['target_price'])}</div>
        <div class="bz-trade-sub" style="color:{ag}">+{sig['profit_potential']:.1f}%</div>
      </div>
      <div class="bz-trade-cell">
        <div class="bz-trade-label">Stop Loss</div>
        <div class="bz-trade-val" style="color:#ff4d6a">{fmt_inr(sig['stop_loss'])}</div>
        <div class="bz-trade-sub" style="color:#ff4d6a">R:R {sig['rr_ratio']:.2f}x</div>
      </div>
      <div class="bz-trade-cell">
        <div class="bz-trade-label">Hold</div>
        <div class="bz-trade-val" style="font-size:12px">{sig['hold_duration']}</div>
        <div class="bz-trade-sub">Duration</div>
      </div>
    </div>

    <div style="margin-bottom:10px">{votes_html}</div>

    <div style="background:{reasoning_bg};border-radius:8px;padding:10px 12px;font-size:10px;color:#8b949e;line-height:1.7;border-left:2px solid {sc_color};margin-bottom:10px">
      📌 {line1}<br>📌 {line2}
    </div>

    <div style="background:{reasoning_bg};border:1px solid {bd};border-radius:8px;padding:10px 12px">
      <div style="display:flex;justify-content:space-between;font-size:9px;font-weight:700;text-transform:uppercase;color:#6b7a94;margin-bottom:6px">
        <span>Intensity</span><span style="color:{sc_color}">{signal}</span>
      </div>
      <div style="display:flex;gap:3px">{''.join(segs)}</div>
      <div style="display:flex;justify-content:space-between;font-size:8px;color:#6b7a94;margin-top:4px"><span>Strong Buy</span><span>Strong Sell</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Visual Metrics ────────────────────────────────────────
    st.markdown('<div class="bz-panel-title">Visual Metrics</div>', unsafe_allow_html=True)
    render_visual_metrics(
        ind["rsi"], sig["success_prob"], sig["rr_ratio"],
        price_data["closes"], ind["period_return"]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Technical Indicators ──────────────────────────────────
    st.markdown('<div class="bz-panel-title">📐 Technical Indicators</div>', unsafe_allow_html=True)
    rsi    = ind["rsi"];    macd  = ind["macd"]
    boll   = ind["bollinger"]; ema50  = ind["ema50"]; ema200 = ind["ema200"]
    rsi_v  = f"{rsi:.2f}"           if rsi            else "—"
    macd_v = f"{macd['hist']:.4f}"  if macd["hist"]   else "—"
    boll_v = f"{boll['pct']:.1f}%"  if boll["pct"]    else "—"
    sk_v   = f"{ind['stoch_k']:.1f}%" if ind["stoch_k"] else "—"

    rsi_r  = ("Overbought", "bz-badge-bear") if rsi and rsi > 70 else ("Oversold", "bz-badge-bull") if rsi and rsi < 30 else ("Neutral", "bz-badge-neut")
    macd_r = ("Bullish ▲", "bz-badge-bull") if macd["hist"] and macd["hist"] > 0 else ("Bearish ▼", "bz-badge-bear")
    ema_r  = ("Golden Cross ▲", "bz-badge-bull") if ema50 and ema200 and ema50 > ema200 else ("Death Cross ▼", "bz-badge-bear") if ema50 and ema200 else ("—", "bz-badge-neut")
    sk_r   = ("Overbought", "bz-badge-bear") if ind["stoch_k"] and ind["stoch_k"] > 80 else ("Oversold", "bz-badge-bull") if ind["stoch_k"] and ind["stoch_k"] < 20 else ("Neutral", "bz-badge-neut")

    st.markdown("".join([
        ind_row_html("RSI (14)",        rsi_v,            *rsi_r),
        ind_row_html("MACD Histogram",  macd_v,           *macd_r),
        ind_row_html("Bollinger %B",    boll_v,           boll["position"], badge_cls(boll["position"])),
        ind_row_html("EMA 50",          fmt_inr(ema50),   f"{'Above' if ema50 and curr > ema50 else 'Below'} EMA50", "bz-badge-bull" if ema50 and curr > ema50 else "bz-badge-bear"),
        ind_row_html("EMA 200",         fmt_inr(ema200),  *ema_r),
        ind_row_html("ATR (14)",        fmt_inr(ind["atr"]), "Volatility", "bz-badge-neut"),
        ind_row_html("Stochastic K",    sk_v,             *sk_r),
        ind_row_html("Volume Trend",    ind["volume_trend"]),
        ind_row_html("Trend",           ind["trend"]),
        ind_row_html("Candlestick",     ind["pattern"]),
        ind_row_html("Candles used",    str(ind["candles"])),
    ]), unsafe_allow_html=True)

    # ── News links ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    link_c = "#4d9fff" if is_neon() else "#2563eb"
    gl, ml = get_news_link(ticker, stock["fullName"])
    st.markdown(f'<div style="font-size:10px;color:#6b7a94;line-height:2">🔗 <a href="{gl}" target="_blank" style="color:{link_c}">Google News</a> · <a href="{ml}" target="_blank" style="color:{link_c}">MoneyControl</a> · <a href="https://economictimes.indiatimes.com/markets/stocks/news" target="_blank" style="color:{link_c}">ET Markets</a></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  FUNDAMENTALS — all rows rendered via module-level ind_row_html
# ══════════════════════════════════════════════════════════════
def render_fundamentals(price_data, ticker, stock):
    pe  = price_data.get("pe_ratio")
    eps = price_data.get("eps")
    mc  = price_data.get("market_cap")
    rg  = price_data.get("revenue_growth")
    de  = price_data.get("debt_equity")
    roe = price_data.get("roe")
    dy  = price_data.get("dividend_yield")
    sec = price_data.get("sector")
    bv  = price_data.get("book_value")
    pb  = price_data.get("price_to_book")
    cr  = price_data.get("current_ratio")
    pm  = price_data.get("profit_margins")

    rows = [
        ind_row_html("P/E Ratio",      f"{pe:.1f}" if pe else "—",          "High" if pe and pe > 30 else "Moderate" if pe else "", "bz-badge-warn" if pe and pe > 30 else "bz-badge-neut"),
        ind_row_html("EPS",            f"₹{eps:.2f}" if eps else "—"),
        ind_row_html("Market Cap",     f"₹{mc/1e7:.0f} Cr" if mc else "—"),
        ind_row_html("Revenue Growth", f"{rg*100:.1f}%" if rg else "—",     "Positive" if rg and rg > 0 else "", "bz-badge-bull" if rg and rg > 0 else "bz-badge-neut"),
        ind_row_html("Debt / Equity",  f"{de:.2f}" if de else "—",          "High" if de and de > 1 else "", "bz-badge-warn" if de and de > 1 else "bz-badge-neut"),
        ind_row_html("ROE",            f"{roe*100:.1f}%" if roe else "—",   "Strong" if roe and roe > 0.15 else "", "bz-badge-bull" if roe and roe > 0.15 else "bz-badge-neut"),
        ind_row_html("Dividend Yield", f"{dy*100:.2f}%" if dy else "—"),
        ind_row_html("Book Value",     f"₹{bv:.2f}" if bv else "—"),
        ind_row_html("Price/Book",     f"{pb:.2f}x" if pb else "—"),
        ind_row_html("Current Ratio",  f"{cr:.2f}" if cr else "—"),
        ind_row_html("Profit Margin",  f"{pm*100:.1f}%" if pm else "—"),
        ind_row_html("Sector",         sec or "—"),
        ind_row_html("52W High",       fmt_inr(price_data.get("52w_high"))),
        ind_row_html("52W Low",        fmt_inr(price_data.get("52w_low"))),
        ind_row_html("Data Source",    price_data["source"]),
    ]
    st.markdown("".join(rows), unsafe_allow_html=True)

    if not any([pe, eps, mc, roe, de]):
        link_c = "#4d9fff" if is_neon() else "#2563eb"
        _, ml   = get_news_link(ticker, stock["fullName"])
        st.markdown(f'<div style="font-size:10px;color:#6b7a94;margin-top:6px">⚠️ Fundamental data unavailable. <a href="{ml}" target="_blank" style="color:{link_c}">View on MoneyControl</a></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  SIGNAL HISTORY TABLE
# ══════════════════════════════════════════════════════════════
def render_signal_history_table(ticker):
    history = st.session_state.signal_history.get(ticker, [])
    if not history:
        st.caption("No history yet — run Analyse a few times to build it.")
        return

    rows = ""
    for h in reversed(history):
        sig = h["signal"]
        sc  = SIGNAL_CONFIG.get(sig, SIGNAL_CONFIG["WAIT"])
        sc_c = sig_color(sc); sc_b = sig_bg(sc); sc_br = sig_border(sc)
        chg_c = (acc_green() if h.get("change_pct", 0) >= 0 else "#ff4d6a")
        chg_s = "+" if h.get("change_pct", 0) >= 0 else ""
        rows += (f'<tr>'
                 f'<td style="color:#6b7a94">{h["time"]}</td>'
                 f'<td style="font-weight:600">{h["tf"]}</td>'
                 f'<td>₹{h["price"]:,.2f} <span style="color:{chg_c};font-size:10px">({chg_s}{h.get("change_pct",0):.2f}%)</span></td>'
                 f'<td><span style="background:{sc_b};color:{sc_c};border:1px solid {sc_br};padding:2px 7px;border-radius:20px;font-size:9px;font-weight:700">{sc["icon"]} {sig}</span></td>'
                 f'<td style="color:#6b7a94">{h.get("regime","—")}</td>'
                 f'<td style="color:{acc_green()}">₹{h.get("target",0):,.2f}</td>'
                 f'<td style="color:#ff4d6a">₹{h.get("stop",0):,.2f}</td>'
                 f'<td>{h.get("prob",0):.0f}%</td>'
                 f'</tr>')

    st.markdown(f"""
    <table class="bz-hist-table">
      <thead><tr>
        <th>Time</th><th>TF</th><th>Price</th><th>Signal</th>
        <th>Regime</th><th>Target</th><th>Stop</th><th>Prob</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  CHART TOGGLE BAR
# ══════════════════════════════════════════════════════════════
def render_chart_toggle_bar():
    c1, c2, c3, _ = st.columns([1, 1, 1.4, 3])
    with c1:
        lbl  = "EMA 50 ✓" if st.session_state.chart_show_ema50 else "EMA 50"
        t    = "primary" if st.session_state.chart_show_ema50 else "secondary"
        if st.button(lbl, key="t_ema50", use_container_width=True, type=t):
            st.session_state.chart_show_ema50 = not st.session_state.chart_show_ema50; st.rerun()
    with c2:
        lbl  = "EMA 200 ✓" if st.session_state.chart_show_ema200 else "EMA 200"
        t    = "primary" if st.session_state.chart_show_ema200 else "secondary"
        if st.button(lbl, key="t_ema200", use_container_width=True, type=t):
            st.session_state.chart_show_ema200 = not st.session_state.chart_show_ema200; st.rerun()
    with c3:
        lbl  = "Bollinger ✓" if st.session_state.chart_show_bb else "Bollinger"
        t    = "primary" if st.session_state.chart_show_bb else "secondary"
        if st.button(lbl, key="t_bb", use_container_width=True, type=t):
            st.session_state.chart_show_bb = not st.session_state.chart_show_bb; st.rerun()

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    inject_global_css()
    render_sidebar()

    ticker  = st.session_state.selected_ticker
    tf_key  = st.session_state.selected_tf
    stock   = STOCKS[ticker]
    tf      = TIMEFRAMES[tf_key]
    ag      = acc_green()

    # ── Ticker strip (flush, no gap) ──────────────────────────
    render_ticker_strip()

    # ── Welcome screen ────────────────────────────────────────
    if not st.session_state.analyse_clicked:
        st.markdown(f"""
        <div class="bz-price-header">
          <div style="font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px">
            {INDUSTRY_ICONS.get(stock['industry'],'📌')} {stock['fullName']} · NSE · {tf['label']}
          </div>
          <div style="font-size:26px;font-weight:900;color:{ag}">🐂 BullzStock Intelligence</div>
          <div style="font-size:12px;color:#6b7a94;margin-top:4px">
            Select a stock → choose timeframe → click <b style="color:{ag}">⚡ Analyse Now</b> in the sidebar
          </div>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        bd = border_dim(); bp = bg_panel(); tm = text_main()
        with c1:
            st.markdown(f"""<div style="background:{bp};border:1px solid {bd};border-radius:10px;padding:16px 18px">
              <div class="bz-panel-title">How to use</div>
              <div style="font-size:12px;color:{tm};line-height:1.9">
                1. Filter by industry (sidebar top)<br>
                2. Click a stock card to select it — prices shown live<br>
                3. Pick a timeframe: 1D · 1W · 1M · 6M · 9M<br>
                4. Click ⚡ Analyse Now<br>
                5. Review signal, chart, indicators &amp; trade levels
              </div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div style="background:{bp};border:1px solid {bd};border-radius:10px;padding:16px 18px">
              <div class="bz-panel-title">What you get</div>
              <div style="font-size:12px;color:{tm};line-height:1.9">
                📈 TradingView chart — correct stock, dark/light matched<br>
                🎯 Entry · Target · Stop Loss (ATR-based)<br>
                💡 Plain-English signal reasoning<br>
                📊 RSI · Prob · R:R · Sparkline gauges<br>
                📋 Fundamentals · Technical indicators<br>
                🕐 Session signal history
              </div></div>""", unsafe_allow_html=True)
        return

    # ── Fetch ──────────────────────────────────────────────────
    with st.spinner(f"Fetching {tf['label']} data for {stock['fullName']}…"):
        price_data = fetch_market_data(ticker, tf_key)

    if not price_data:
        st.error("⚠️ Data fetch failed. NSE may be closed (Mon–Fri 9:15–15:30 IST) or Yahoo Finance is rate-limiting. Try Clear Cache & Refresh or try again in a minute.")
        return

    ind    = compute_all(price_data)
    sig    = generate_signal(price_data["closes"], price_data["highs"],
                             price_data["lows"], price_data["volumes"], ind)
    curr   = price_data["current_price"]
    chg_up = price_data["change"] >= 0
    signal = sig["signal"]
    sc     = SIGNAL_CONFIG.get(signal, SIGNAL_CONFIG["WAIT"])

    update_signal_history(ticker, {
        "time": datetime.now().strftime("%H:%M:%S"), "tf": tf["label"],
        "price": curr, "change_pct": price_data["change_pct"],
        "signal": signal, "regime": sig["regime"],
        "target": sig["target_price"], "stop": sig["stop_loss"],
        "prob": sig["success_prob"],
    })

    sc_color = sig_color(sc)
    chg_sym  = "▲" if chg_up else "▼"
    chg_col  = ag if chg_up else "#ff4d6a"

    # ── Price header ──────────────────────────────────────────
    bd = border_dim(); bp = bg_panel(); tm = text_main()
    st.markdown(f"""
    <div class="bz-price-header" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
      <div>
        <div style="font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:5px">Signal · {tf['label']} · {sig['regime']}</div>
        <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap">
          <div style="font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:700;color:{tm}">₹{curr:,.2f}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;color:{chg_col}">
            {chg_sym} ₹{abs(price_data['change']):.2f} ({abs(price_data['change_pct']):.2f}%)
          </div>
        </div>
        <div style="font-size:10px;color:#6b7a94;margin-top:3px">{stock['fullName']} · NSE · Prev ₹{price_data['prev_close']:,.2f}</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:9px;color:#6b7a94">{price_data['time']} IST · {price_data['source']}</div>
        <div style="margin-top:6px;background:{sig_bg(sc)};color:{sc_color};border:1px solid {sig_border(sc)};
                    padding:4px 14px;border-radius:20px;font-size:11px;font-weight:800;display:inline-block">
          {sc['icon']} {signal}
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── OHLCV ─────────────────────────────────────────────────
    render_ohlcv(price_data)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3:1 layout — chart left, signal right ─────────────────
    col_main, col_right = st.columns([3, 1])

    with col_main:
        render_chart_toggle_bar()
        render_tradingview_chart(
            stock["tv"], tf["tv_interval"],
            st.session_state.chart_show_ema50,
            st.session_state.chart_show_ema200,
            st.session_state.chart_show_bb,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Indicators + Fundamentals ──────────────────────────
        col_ind, col_fund = st.columns(2)

        with col_ind:
            st.markdown(f'<div class="bz-panel-title">📐 Technical Indicators</div>', unsafe_allow_html=True)
            rsi    = ind["rsi"];    macd   = ind["macd"]
            boll   = ind["bollinger"]; ema50 = ind["ema50"]; ema200 = ind["ema200"]
            rsi_v  = f"{rsi:.2f}"           if rsi            else "—"
            macd_v = f"{macd['hist']:.4f}"  if macd["hist"]   else "—"
            boll_v = f"{boll['pct']:.1f}%"  if boll["pct"]    else "—"
            sk_v   = f"{ind['stoch_k']:.1f}%" if ind["stoch_k"] else "—"

            rsi_r  = ("Overbought", "bz-badge-bear") if rsi and rsi > 70 else ("Oversold", "bz-badge-bull") if rsi and rsi < 30 else ("Neutral", "bz-badge-neut")
            macd_r = ("Bullish ▲", "bz-badge-bull") if macd["hist"] and macd["hist"] > 0 else ("Bearish ▼", "bz-badge-bear")
            ema_r  = ("Golden Cross ▲", "bz-badge-bull") if ema50 and ema200 and ema50 > ema200 else ("Death Cross ▼", "bz-badge-bear") if ema50 and ema200 else ("—", "bz-badge-neut")
            sk_r   = ("Overbought", "bz-badge-bear") if ind["stoch_k"] and ind["stoch_k"] > 80 else ("Oversold", "bz-badge-bull") if ind["stoch_k"] and ind["stoch_k"] < 20 else ("Neutral", "bz-badge-neut")
            pr     = ind["period_return"]

            st.markdown("".join([
                ind_row_html("RSI (14)",       rsi_v,           *rsi_r),
                ind_row_html("MACD Histogram", macd_v,          *macd_r),
                ind_row_html("Bollinger %B",   boll_v,          boll["position"], badge_cls(boll["position"])),
                ind_row_html("EMA 50",         fmt_inr(ema50),  f"{'Above' if ema50 and curr>ema50 else 'Below'} EMA50", "bz-badge-bull" if ema50 and curr > ema50 else "bz-badge-bear"),
                ind_row_html("EMA 200",        fmt_inr(ema200), *ema_r),
                ind_row_html("ATR (14)",       fmt_inr(ind["atr"]), "Volatility", "bz-badge-neut"),
                ind_row_html("Stochastic K",   sk_v,            *sk_r),
                ind_row_html("Period Return",  fmt_pct(pr)),
                ind_row_html("Volume Trend",   ind["volume_trend"]),
                ind_row_html("Trend",          ind["trend"]),
                ind_row_html("Candlestick",    ind["pattern"]),
                ind_row_html("Candles used",   str(ind["candles"])),
            ]), unsafe_allow_html=True)

        with col_fund:
            st.markdown(f'<div class="bz-panel-title">📋 Fundamentals</div>', unsafe_allow_html=True)
            render_fundamentals(price_data, ticker, stock)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Signal History ─────────────────────────────────────
        st.markdown(f'<div class="bz-panel-title">🕐 Signal History · Session</div>', unsafe_allow_html=True)
        render_signal_history_table(ticker)

    with col_right:
        render_right_panel(sig, ind, price_data, stock, tf, ticker)

    # ── Telegram alert ────────────────────────────────────────
    if curr >= sig["target_price"] * 0.98:
        msg = (f"🎯 <b>Target Alert — {ticker}</b>\n\n"
               f"Current: {fmt_inr(curr)}\n"
               f"Target: {fmt_inr(sig['target_price'])}\n"
               f"Signal: {signal}\n"
               f"Profit: +{sig['profit_potential']:.1f}%\n"
               f"Probability: {sig['success_prob']:.0f}%")
        ok, err = send_telegram(msg)
        if ok:
            st.success("🎯 Target reached! Telegram alert sent.")
        else:
            if "not configured" not in err:
                st.warning(f"Target reached but Telegram failed: {err}")

    # ── Disclaimer ────────────────────────────────────────────
    st.markdown(f"""
    <div class="bz-disclaimer">
      ⚠️ Data from {price_data['source']}. Signals are rule-based indicator confluence —
      <b>not financial advice</b>. Always consult a SEBI-registered investment advisor.
      NSE hours: Mon–Fri 9:15 AM – 3:30 PM IST.
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

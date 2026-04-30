#!/usr/bin/env python3
"""
MB Stock Intelligence — v3
Fixes: theme-aware UI, TradingView embed chart, signal reasoning,
       polished sidebar, fundamentals fallback, news reference link
"""

import math
import requests
import streamlit as st
from datetime import datetime
import os
import tempfile

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
    page_title="MB Stock Intelligence",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded",
)



# ── Theme-aware CSS (works on both light & dark Streamlit themes) ──
st.markdown("""
<style>
  /* Metric cards — transparent so they inherit Streamlit's theme */
  .mb-card {
    background: var(--background-color, transparent);
    border: 1px solid var(--secondary-background-color, #e9ecef);
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
  }
  .mb-card-label {
    font-size: 11px;
    color: var(--text-color-muted, #6c757d);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
  }
  .mb-card-value {
    font-size: 20px;
    font-weight: 700;
    margin: 0;
  }
  .mb-card-sub {
    font-size: 11px;
    color: var(--text-color-muted, #6c757d);
    margin-top: 3px;
  }
  /* Signal box */
  .signal-box {
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 1rem;
  }
  .vote-item { font-size: 13px; padding: 2px 0; }
  /* Indicator rows */
  .ind-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid var(--secondary-background-color, #f0f0f0);
    font-size: 13px;
  }
  .ind-label { color: var(--text-color-muted, #6c757d); }
  /* Sidebar stock card */
  .sb-stock-card {
    background: var(--secondary-background-color, #f8f9fa);
    border-radius: 8px;
    padding: 10px 12px;
    margin: 6px 0;
    border-left: 3px solid #1a7340;
    font-size: 12px;
  }
  /* Signal reasoning box */
  .reasoning-box {
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    background: var(--secondary-background-color, #f8f9fa);
    border: 1px solid var(--secondary-background-color, #e9ecef);
    font-size: 13px;
    line-height: 1.6;
  }
  /* Visual metric cards — theme-aware dark-style panels */
  .vm-card {
    border-radius: 10px;
    padding: 14px 10px 10px;
    text-align: center;
    border: 1px solid var(--secondary-background-color, #e0e0e0);
    background: var(--secondary-background-color, #f8f9fa);
  }
  .vm-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-color-muted, #6c757d);
    margin-bottom: 6px;
  }
  .vm-value {
    font-size: 22px;
    font-weight: 700;
    margin: 4px 0 2px;
  }
  .vm-sub {
    font-size: 11px;
    color: var(--text-color-muted, #6c757d);
  }
  .disclaimer {
    font-size: 11px;
    color: var(--text-color-muted, #999);
    margin-top: 1rem;
    padding: 10px 14px;
    background: var(--secondary-background-color, #f8f9fa);
    border-radius: 8px;
  }
  /* Toggle buttons */
  div[data-testid="column"] button {
    border-radius: 20px !important;
    font-size: 12px !important;
  }
</style>
""", unsafe_allow_html=True)

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
    "STRONG BUY":  {"color": "#1a7340", "bg": "#d4edda", "border": "#28a745", "icon": "▲▲"},
    "BUY":         {"color": "#155724", "bg": "#d4edda", "border": "#5cb85c", "icon": "▲"},
    "SHORT SELL":  {"color": "#721c24", "bg": "#f8d7da", "border": "#dc3545", "icon": "▼▼"},
    "SELL":        {"color": "#721c24", "bg": "#f8d7da", "border": "#e06c75", "icon": "▼"},
    "HOLD":        {"color": "#004085", "bg": "#cce5ff", "border": "#007bff", "icon": "▬"},
    "WAIT":        {"color": "#856404", "bg": "#fff3cd", "border": "#ffc107", "icon": "◌"},
}

# ── Session state ─────────────────────────────────────────────
for key, default in [
    ("signal_history", {}),
    ("chart_show_ema50", True),
    ("chart_show_ema200", True),
    ("chart_show_bb", True),
]:
    if key not in st.session_state:
        st.session_state[key] = default

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

# ── Technical Indicators ──────────────────────────────────────
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
        "ema9":          calc_ema(c, min(9,   len(c))),
        "ema21":         calc_ema(c, min(21,  len(c))),
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

# ── Signal Engine ─────────────────────────────────────────────
def generate_signal(closes, highs, lows, volumes, ind):
    rsi     = ind["rsi"];  macd    = ind["macd"]
    boll    = ind["bollinger"]; ema50   = ind["ema50"]
    ema200  = ind["ema200"];    atr     = ind["atr"]
    trend   = ind["trend"];     stoch_k = ind["stoch_k"]
    curr    = closes[-1]
    score = 0; max_score = 0; votes = []

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
    if "Strong Uptrend"   in trend: score += 2; votes.append("Strong Uptrend confirmed")
    elif "Mild Uptrend"   in trend: score += 1; votes.append("Mild Uptrend")
    elif "Strong Downtrend" in trend: score -= 2; votes.append("Strong Downtrend confirmed")
    elif "Mild Downtrend" in trend: score -= 1; votes.append("Mild Downtrend")
    else:                           votes.append("Sideways / Range-bound market")

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

# ── Signal Reasoning (2-line plain English summary) ──────────
def build_signal_reasoning(sig, ind, price_data):
    signal   = sig["signal"]
    rsi      = ind["rsi"]
    macd     = ind["macd"]
    ema50    = ind["ema50"]
    ema200   = ind["ema200"]
    trend    = ind["trend"]
    boll     = ind["bollinger"]
    curr     = price_data["current_price"]
    votes    = sig["votes"]

    # Build 2-line reasoning
    bullish_reasons  = [v for v in votes if "Bullish" in v or "Uptrend" in v or "confirm" in v and "bearish" not in v.lower()]
    bearish_reasons  = [v for v in votes if "Bearish" in v or "Downtrend" in v]

    if signal in ("STRONG BUY", "BUY"):
        top = bullish_reasons[:2] if bullish_reasons else votes[:2]
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

# ── News Reference Link ───────────────────────────────────────
def get_news_link(ticker_symbol, full_name):
    encoded = full_name.replace(" ", "+")
    google_news = f"https://news.google.com/search?q={encoded}+NSE+stock&hl=en-IN&gl=IN"
    moneycontrol = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data={ticker_symbol}&cid=&mbsearch_str=&type_search=News&news_op=&tagnews=y&sel_news=MNC"
    return google_news, moneycontrol

# ── Data Fetching ─────────────────────────────────────────────
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
                        "open":   meta.get("regularMarketOpen",    opens[-1]  if opens   else curr),
                        "high":   meta.get("regularMarketDayHigh", highs[-1]  if highs   else curr),
                        "low":    meta.get("regularMarketDayLow",  lows[-1]   if lows    else curr),
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
                        "sector": None,
                    }
    except Exception as e:
        st.warning(f"Direct Yahoo error: {e}")

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

        # Fundamentals with multiple fallback keys
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
        st.warning(f"yfinance error: {e}")
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
    except Exception as e:
        st.warning(f"Alpha Vantage error: {e}")
        return None

def fetch_market_data(ticker, tf_key):
    tf    = TIMEFRAMES[tf_key]
    stock = STOCKS[ticker]
    data  = fetch_via_yfinance(stock["yf"], tf["yf_period"], tf["yf_interval"])
    if not data:
        data = fetch_via_alphavantage(stock["av"], tf["av_func"], tf["av_interval"])
    return data

# ── Telegram ──────────────────────────────────────────────────
def send_telegram(message):
    url = "https://api.telegram.org/bot" + TG_TOKEN + "/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT, "text": message}, timeout=10)
        return r.status_code == 200
    except:
        return False

# ── Signal History ────────────────────────────────────────────
def update_signal_history(ticker, rec):
    if ticker not in st.session_state.signal_history:
        st.session_state.signal_history[ticker] = []
    h = st.session_state.signal_history[ticker]
    if h and h[-1]["time"] == rec["time"]: h[-1] = rec
    else: h.append(rec)
    st.session_state.signal_history[ticker] = h[-10:]

def render_signal_history(ticker):
    history = st.session_state.signal_history.get(ticker, [])
    if not history:
        st.caption("No history yet — run Analyse a few times to build it.")
        return
    rows_html = ""
    for i, h in enumerate(reversed(history)):
        sig = h["signal"]; sc = SIGNAL_CONFIG.get(sig, SIGNAL_CONFIG["HOLD"])
        badge = f'<span style="background:{sc["bg"]};color:{sc["color"]};border:1px solid {sc["border"]};padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600">{sc["icon"]} {sig}</span>'
        chg_c = "#1a7340" if h.get("change_pct", 0) >= 0 else "#721c24"
        chg_s = "+" if h.get("change_pct", 0) >= 0 else ""
        bg    = "background:#f8f9fa" if i % 2 == 0 else ""
        rows_html += f"""<tr style="{bg}">
            <td style="padding:6px 10px;font-size:12px">{h['time']}</td>
            <td style="padding:6px 10px;font-size:12px"><b>{h['tf']}</b></td>
            <td style="padding:6px 10px;font-size:12px">₹{h['price']:,.2f} <span style="color:{chg_c};font-size:11px">({chg_s}{h.get('change_pct',0):.2f}%)</span></td>
            <td style="padding:6px 10px">{badge}</td>
            <td style="padding:6px 10px;font-size:12px;color:{chg_c}">{h.get('regime','—')}</td>
            <td style="padding:6px 10px;font-size:12px">₹{h.get('target',0):,.2f}</td>
            <td style="padding:6px 10px;font-size:12px">₹{h.get('stop',0):,.2f}</td>
            <td style="padding:6px 10px;font-size:12px">{h.get('prob',0):.0f}%</td>
        </tr>"""
    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;font-size:12px">
      <thead><tr style="background:#f1f3f5;border-bottom:2px solid #dee2e6">
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Time</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">TF</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Price</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Signal</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Regime</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Target</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Stop</th>
        <th style="padding:6px 10px;text-align:left;font-size:11px;color:#6c757d;text-transform:uppercase">Prob</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

# ── UI Helpers ────────────────────────────────────────────────
def metric_card(label, value, sub=None, value_color="#212529"):
    sub_html = f'<div class="mb-card-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="mb-card">
      <div class="mb-card-label">{label}</div>
      <div class="mb-card-value" style="color:{value_color}">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)

def indicator_row(label, value, reading="", reading_color="inherit"):
    reading_html = f'<span style="color:{reading_color};font-weight:600">{reading}</span>' if reading else ""
    st.markdown(f"""
    <div class="ind-row">
      <span class="ind-label">{label}</span>
      <span>{value} {reading_html}</span>
    </div>""", unsafe_allow_html=True)

# ── TradingView Widget Chart ──────────────────────────────────
def render_tradingview_chart(tv_symbol, tv_interval, show_ema50, show_ema200, show_bb):
    studies = []
    if show_ema50:  studies.append('"MAExp@tv-basicstudies"')
    if show_ema200: studies.append('"MAExp@tv-basicstudies"')
    if show_bb:     studies.append('"BB@tv-basicstudies"')
    studies_str = "[" + ",".join(studies) + "]"

    widget_html = f"""
    <div class="tradingview-widget-container" style="height:520px;width:100%">
      <div id="tradingview_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "{tv_interval}",
        "timezone": "Asia/Kolkata",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "withdateranges": true,
        "hide_side_toolbar": false,
        "allow_symbol_change": false,
        "save_image": false,
        "studies": {studies_str},
        "container_id": "tradingview_chart",
        "hide_top_toolbar": false,
        "hide_legend": false,
        "show_popup_button": true,
        "popup_width": "1000",
        "popup_height": "650"
      }});
      </script>
    </div>"""
    st.components.v1.html(widget_html, height=530, scrolling=False)

# ── Visual Metrics (theme-aware HTML/SVG) ─────────────────────
def render_visual_metrics(rsi_val, prob_val, rr_ratio, closes, period_return):
    rsi_color  = "#dc3545" if (rsi_val or 50) > 70 else "#1a7340" if (rsi_val or 50) < 30 else "#f59e0b"
    rsi_label  = "Overbought" if (rsi_val or 50) > 70 else "Oversold" if (rsi_val or 50) < 30 else "Neutral"
    rsi_disp   = f"{rsi_val:.1f}" if rsi_val else "—"
    prob_color = "#1a7340" if prob_val >= 65 else "#f59e0b" if prob_val >= 45 else "#dc3545"
    rr_color   = "#1a7340" if rr_ratio >= 2 else "#f59e0b" if rr_ratio >= 1 else "#dc3545"
    pr_color   = "#1a7340" if (period_return or 0) >= 0 else "#dc3545"
    pr_text    = fmt_pct(period_return) if period_return is not None else "—"

    def gauge_arc(val, max_val, color, label, disp, sub):
        pct   = min(val / max_val, 1.0)
        angle = pct * 180 - 180
        rad   = math.radians(angle)
        nx    = 60 + 38 * math.cos(rad)
        ny    = 52 + 38 * math.sin(rad)
        ex    = 60 + 50 * math.cos(math.radians(pct * 180 - 180))
        ey    = 52 + 50 * math.sin(math.radians(pct * 180 - 180))
        large = 1 if pct > 0.5 else 0
        return f"""
        <div class="vm-card">
          <div class="vm-label">{label}</div>
          <svg viewBox="0 0 120 62" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:130px">
            <path d="M10 52 A50 50 0 0 1 110 52" fill="none" stroke="#e9ecef" stroke-width="9" stroke-linecap="round"/>
            <path d="M10 52 A50 50 0 {large} 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round"/>
            <line x1="60" y1="52" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="60" cy="52" r="4" fill="{color}"/>
          </svg>
          <div class="vm-value" style="color:{color}">{disp}</div>
          <div class="vm-sub">{sub}</div>
        </div>"""

    rsi_html  = gauge_arc(rsi_val or 50, 100, rsi_color, "RSI (14)", rsi_disp, rsi_label)
    prob_html = gauge_arc(prob_val, 100, prob_color, "Success Prob.", f"{prob_val:.0f}%",
                          "High confidence" if prob_val >= 65 else "Moderate" if prob_val >= 45 else "Low confidence")

    # Donut
    total = 1 + max(rr_ratio, 0.01)
    circ  = 2 * math.pi * 28
    rd    = (1 / total) * circ
    rwd   = (max(rr_ratio, 0.01) / total) * circ
    rr_html = f"""
    <div class="vm-card">
      <div class="vm-label">Risk : Reward</div>
      <svg viewBox="0 0 80 76" xmlns="http://www.w3.org/2000/svg" style="width:80px;height:76px;display:block;margin:0 auto">
        <circle cx="40" cy="40" r="28" fill="none" stroke="#dc3545" stroke-width="9"
                stroke-dasharray="{rd:.1f} {circ:.1f}" stroke-dashoffset="0" transform="rotate(-90 40 40)"/>
        <circle cx="40" cy="40" r="28" fill="none" stroke="#1a7340" stroke-width="9"
                stroke-dasharray="{rwd:.1f} {circ:.1f}" stroke-dashoffset="{-rd:.1f}" transform="rotate(-90 40 40)"/>
        <text x="40" y="37" text-anchor="middle" font-size="8.5" fill="{rr_color}" font-weight="700" font-family="sans-serif">1:{rr_ratio:.1f}</text>
        <text x="40" y="48" text-anchor="middle" font-size="7" fill="#6c757d" font-family="sans-serif">R:R</text>
      </svg>
      <div class="vm-value" style="color:{rr_color};font-size:16px">1 : {rr_ratio:.2f}</div>
      <div class="vm-sub">{'Good ≥2x' if rr_ratio >= 2 else 'Fair 1–2x' if rr_ratio >= 1 else 'Poor <1x'}</div>
    </div>"""

    # Sparkline
    spark_svg = ""
    if closes and len(closes) > 1:
        mn, mx = min(closes), max(closes)
        rng    = mx - mn if mx != mn else 1
        w, h   = 180, 40
        pts    = [f"{int(i/(len(closes)-1)*w)},{int(h-((c-mn)/rng)*h)}" for i, c in enumerate(closes)]
        spark_svg = f"""<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:42px;display:block">
          <polyline points="{' '.join(pts)}" fill="none" stroke="{pr_color}" stroke-width="1.8" stroke-linejoin="round"/>
        </svg>"""

    spark_html = f"""
    <div class="vm-card">
      <div class="vm-label">Period Return</div>
      <div style="padding:4px 6px 0">{spark_svg}</div>
      <div class="vm-value" style="color:{pr_color}">{pr_text}</div>
      <div class="vm-sub">{'Positive' if (period_return or 0) >= 0 else 'Negative'} over period</div>
    </div>"""

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(rsi_html,   unsafe_allow_html=True)
    with c2: st.markdown(prob_html,  unsafe_allow_html=True)
    with c3: st.markdown(rr_html,    unsafe_allow_html=True)
    with c4: st.markdown(spark_html, unsafe_allow_html=True)

# ── Chart Toggle Bar ──────────────────────────────────────────
def render_chart_toggle_bar():
    c1, c2, c3, _, _, _, _ = st.columns([1.2, 1.2, 1.8, 1, 1, 1, 1])
    with c1:
        lbl = "🟡 EMA 50 ✓" if st.session_state.chart_show_ema50 else "🟡 EMA 50"
        if st.button(lbl, key="t_ema50", use_container_width=True):
            st.session_state.chart_show_ema50 = not st.session_state.chart_show_ema50; st.rerun()
    with c2:
        lbl = "🟣 EMA 200 ✓" if st.session_state.chart_show_ema200 else "🟣 EMA 200"
        if st.button(lbl, key="t_ema200", use_container_width=True):
            st.session_state.chart_show_ema200 = not st.session_state.chart_show_ema200; st.rerun()
    with c3:
        lbl = "🔵 Bollinger Bands ✓" if st.session_state.chart_show_bb else "🔵 Bollinger Bands"
        if st.button(lbl, key="t_bb", use_container_width=True):
            st.session_state.chart_show_bb = not st.session_state.chart_show_bb; st.rerun()

# ── Main App ──────────────────────────────────────────────────
def main():
    # ── Polished Sidebar ──────────────────────────────────────
    with st.sidebar:
        st.markdown("""<style>
        [data-testid="stSidebarNav"] a p,
        [data-testid="stSidebarNavLink"] span,
        [data-testid="stSidebarNavItems"] a,
        nav a span, nav a p {
        }
        </style>""", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:16px 8px 12px">
          <div style="font-size:42px;margin-bottom:6px">🐂</div>
          <div style="font-size:18px;font-weight:800;letter-spacing:0.04em;
              background:linear-gradient(135deg,#58a6ff,#00ff88);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
              MB STOCK INTEL
          </div>
          <div style="font-size:11px;color:#6e7681;margin-top:4px;letter-spacing:0.08em;">
              ENHANCED EDITION · NSE INDIA
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown("---")

        industries = ["All"] + sorted(set(v["industry"] for v in STOCKS.values()))
        chosen_ind = st.selectbox(
            "🏭 Filter by Industry",
            industries,
            format_func=lambda x: f"{INDUSTRY_ICONS.get(x, '📌')} {x}"
        )

        filtered      = {k: v for k, v in STOCKS.items() if chosen_ind == "All" or v["industry"] == chosen_ind}
        ticker_options = list(filtered.keys())
        ticker_labels  = [f"{INDUSTRY_ICONS.get(filtered[t]['industry'],'📌')} {t} — {filtered[t]['name']}" for t in ticker_options]
        ticker_idx     = st.selectbox("📈 Select Stock", range(len(ticker_options)), format_func=lambda i: ticker_labels[i])
        ticker         = ticker_options[ticker_idx]

        tf_key = st.radio(
            "⏱ Timeframe",
            list(TIMEFRAMES.keys()),
            format_func=lambda k: TIMEFRAMES[k]["label"],
            index=2,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        analyse = st.button("🔍  Analyse Now", use_container_width=True, type="primary")

        # Selected stock info card
        s = STOCKS[ticker]
        st.markdown(f"""
        <div class="sb-stock-card">
          <div style="font-weight:700;font-size:13px">{INDUSTRY_ICONS.get(s['industry'],'📌')} {ticker}</div>
          <div style="font-size:12px;margin-top:2px">{s['fullName']}</div>
          <div style="font-size:11px;color:#6c757d;margin-top:4px">
            Industry: {s['industry']}<br>
            Timeframe: {TIMEFRAMES[tf_key]['label']}
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="font-size:11px;color:#6c757d;line-height:1.7">
          <b>🕐 NSE Hours</b><br>
          Mon–Fri · 9:15 AM – 3:30 PM IST<br><br>
          <b>📡 Data Sources</b><br>
          Yahoo Finance · Alpha Vantage<br><br>
          <b>📊 Indicators Used</b><br>
          RSI · MACD · EMA 50/200<br>
          Bollinger Bands · ATR · Stochastic
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑️ Clear Signal History", use_container_width=True):
            st.session_state.signal_history = {}
            st.success("History cleared")

    # ── Header ────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:0.5rem">
      <div style="font-size:44px;line-height:1">🐂</div>
      <div>
        <div style="font-size:26px;font-weight:800;line-height:1.1">MB Stock Intelligence</div>
        <div style="font-size:12px;color:#6c757d">Live NSE · TradingView Charts · Signal Reasoning · Telegram Alerts</div>
      </div>
      <div style="margin-left:auto;background:#1a7340;color:white;padding:3px 12px;border-radius:20px;font-size:11px;font-weight:700">v3 · Enhanced</div>
    </div>
    <hr style="margin:0.4rem 0 1rem">""", unsafe_allow_html=True)

    if not analyse:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("""
            **How to use:**
            1. Select an industry from the sidebar filter
            2. Pick a stock and timeframe
            3. Click **Analyse Now**
            4. Review signal, reasoning, chart and metrics

            **Signals explained:**
            - **STRONG BUY / BUY** — Majority of indicators align bullish
            - **SHORT SELL / SELL** — Majority of indicators align bearish
            - **HOLD** — Mixed signals, maintain position
            - **WAIT** — No clear direction, stay out
            """)
        with col_r:
            st.markdown("""
            **What you get:**
            - 📈 Live TradingView chart with EMA/BB overlays
            - 🎯 Entry price, Target and Stop Loss (ATR-based)
            - 💡 2-line signal reasoning in plain English
            - 🔗 News reference links for the stock
            - 📊 Visual metrics — RSI gauge, R:R donut, sparkline
            - 🕐 Session-based signal history table
            - 📲 Telegram alert when target is hit
            """)
        return

    stock = STOCKS[ticker]
    tf    = TIMEFRAMES[tf_key]

    with st.spinner(f"Fetching {tf['label']} data for {stock['fullName']}..."):
        price_data = fetch_market_data(ticker, tf_key)

    if not price_data:
        st.error("Both Yahoo Finance and Alpha Vantage failed. NSE may be closed (Mon–Fri 9:15–15:30 IST).")
        return

    ind    = compute_all(price_data)
    sig    = generate_signal(price_data["closes"], price_data["highs"],
                             price_data["lows"], price_data["volumes"], ind)
    curr   = price_data["current_price"]
    chg_up = price_data["change"] >= 0
    signal = sig["signal"]
    sc     = SIGNAL_CONFIG.get(signal, SIGNAL_CONFIG["HOLD"])
    macd   = ind["macd"]
    boll   = ind["bollinger"]
    rsi    = ind["rsi"]
    ema50  = ind["ema50"]
    ema200 = ind["ema200"]

    # Save history
    update_signal_history(ticker, {
        "time": datetime.now().strftime("%H:%M:%S"), "tf": tf["label"],
        "price": curr, "change_pct": price_data["change_pct"],
        "signal": signal, "regime": sig["regime"],
        "target": sig["target_price"], "stop": sig["stop_loss"],
        "prob": sig["success_prob"],
    })

    # ── Live price strip ──────────────────────────────────────
    chg_color = "#1a7340" if chg_up else "#721c24"
    chg_sym   = "▲" if chg_up else "▼"
    st.markdown(f"""
    <div style="border-radius:12px;padding:14px 22px;margin-bottom:1rem;
                border:1px solid {'#c3e6cb' if chg_up else '#f5c6cb'};
                background:{'#f0fff4' if chg_up else '#fff5f5'};
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div>
        <div style="font-size:12px;color:#6c757d;font-weight:600;text-transform:uppercase;letter-spacing:0.05em">
          {INDUSTRY_ICONS.get(stock['industry'],'📌')} {stock['fullName']} · NSE · {tf['label']}
        </div>
        <div style="font-size:30px;font-weight:800;margin-top:2px">₹{curr:,.2f}
          <span style="font-size:15px;color:{chg_color};margin-left:8px">{chg_sym} ₹{abs(price_data['change']):.2f} ({abs(price_data['change_pct']):.2f}%)</span>
        </div>
      </div>
      <div style="font-size:11px;color:#6c757d;text-align:right">
        <div>{price_data['time']} IST · {price_data['source']}</div>
        <div>Prev close ₹{price_data['prev_close']:,.2f} · {ind['candles']} candles</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # OHLCV
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: metric_card("Open",     fmt_inr(price_data["open"]))
    with c2: metric_card("High",     fmt_inr(price_data["high"]),          value_color="#1a7340")
    with c3: metric_card("Low",      fmt_inr(price_data["low"]),           value_color="#721c24")
    with c4: metric_card("Volume",   f"{price_data['volume']/1e5:.1f}L")
    with c5: metric_card("52W High", fmt_inr(price_data.get("52w_high")), value_color="#1a7340")
    with c6: metric_card("52W Low",  fmt_inr(price_data.get("52w_low")),  value_color="#721c24")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Signal Box + Reasoning ────────────────────────────────
    confluence  = f"{abs(sig['pct_bull']):.0f}% {'bullish' if sig['pct_bull'] >= 0 else 'bearish'} confluence"
    votes_html  = "".join(f'<div class="vote-item" style="color:#495057">• {v}</div>' for v in sig["votes"])
    line1, line2 = build_signal_reasoning(sig, ind, price_data)
    google_link, mc_link = get_news_link(ticker, stock["fullName"])

    st.markdown(f"""
    <div class="signal-box" style="background:{sc['bg']};border:2px solid {sc['border']}">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
          <div style="font-size:11px;color:{sc['color']};font-weight:700;text-transform:uppercase;letter-spacing:0.06em">
            Signal · {tf['label']} · {sig['regime']}
          </div>
          <div style="font-size:26px;font-weight:800;color:{sc['color']};margin-top:4px">{sc['icon']} {signal}</div>
          <div style="font-size:12px;color:{sc['color']};margin-top:2px">{confluence}</div>
        </div>
        <div style="max-width:400px">{votes_html}</div>
      </div>
    </div>
    <div class="reasoning-box">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#6c757d;letter-spacing:0.05em;margin-bottom:6px">
        💡 Signal Reasoning
      </div>
      <div>📌 {line1}</div>
      <div style="margin-top:4px">📌 {line2}</div>
      <div style="margin-top:8px;font-size:12px;color:#6c757d">
        🔗 News: <a href="{google_link}" target="_blank" style="color:#004085;text-decoration:none">Google News</a>
        &nbsp;·&nbsp;
        <a href="{mc_link}" target="_blank" style="color:#004085;text-decoration:none">MoneyControl</a>
        &nbsp;·&nbsp;
        <a href="https://economictimes.indiatimes.com/markets/stocks/news" target="_blank" style="color:#004085;text-decoration:none">Economic Times</a>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Trade Levels ──────────────────────────────────────────
    st.markdown("### 🎯 Trade Levels")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Buy / Entry",   fmt_inr(sig["buy_price"]),    value_color="#004085")
    with c2: metric_card("Target Price",  fmt_inr(sig["target_price"]), value_color="#1a7340")
    with c3: metric_card("Stop Loss",     fmt_inr(sig["stop_loss"]),    value_color="#721c24")
    with c4: metric_card("Hold Duration", sig["hold_duration"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Visual Metrics ────────────────────────────────────────
    st.markdown("### 📊 Visual Metrics")
    render_visual_metrics(rsi, sig["success_prob"], sig["rr_ratio"],
                          price_data["closes"], ind["period_return"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TradingView Chart ─────────────────────────────────────
    st.markdown("### 📈 Live Chart")
    st.caption("Powered by TradingView · Use the toolbar to zoom, draw or add indicators")
    render_chart_toggle_bar()
    render_tradingview_chart(
        stock["tv"], tf["tv_interval"],
        st.session_state.chart_show_ema50,
        st.session_state.chart_show_ema200,
        st.session_state.chart_show_bb,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Indicators + Fundamentals ─────────────────────────────
    col_ind, col_fund = st.columns(2)

    with col_ind:
        st.markdown("#### 📐 Technical Indicators")
        rsi_val  = f"{rsi:.2f}"           if rsi             else "—"
        macd_val = f"{macd['hist']:.4f}"  if macd["hist"]    else "—"
        boll_val = f"{boll['pct']:.1f}%"  if boll["pct"]     else "—"
        sk_val   = f"{ind['stoch_k']:.1f}%" if ind["stoch_k"] else "—"
        pr       = ind["period_return"]

        rsi_read  = ("Overbought", "#721c24") if rsi and rsi > 70 else ("Oversold", "#1a7340") if rsi and rsi < 30 else ("Neutral", "#495057")
        macd_read = ("Bullish ▲", "#1a7340") if macd["hist"] and macd["hist"] > 0 else ("Bearish ▼", "#721c24")
        ema_read  = ("Golden Cross ▲", "#1a7340") if ema50 and ema200 and ema50 > ema200 else ("Death Cross ▼", "#721c24") if ema50 and ema200 else ("N/A", "#6c757d")
        sk_read   = ("Overbought", "#721c24") if ind["stoch_k"] and ind["stoch_k"] > 80 else ("Oversold", "#1a7340") if ind["stoch_k"] and ind["stoch_k"] < 20 else ("Neutral", "#495057")

        indicator_row("RSI (14)",       rsi_val,  *rsi_read)
        indicator_row("MACD Histogram", macd_val, *macd_read)
        indicator_row("Bollinger %B",   boll_val, boll["position"])
        indicator_row("EMA 50",         fmt_inr(ema50),  f"Price {'above' if ema50 and curr > ema50 else 'below'} EMA50" if ema50 else "—")
        indicator_row("EMA 200",        fmt_inr(ema200), *ema_read)
        indicator_row("ATR (14)",       fmt_inr(ind["atr"]), "Volatility measure")
        indicator_row("Stochastic K",   sk_val, *sk_read)
        indicator_row("Period Return",  fmt_pct(pr), "▲" if pr and pr >= 0 else "▼", "#1a7340" if pr and pr >= 0 else "#721c24")
        indicator_row("Volume Trend",   ind["volume_trend"])
        indicator_row("Trend",          ind["trend"])
        indicator_row("Candlestick",    ind["pattern"])
        indicator_row("Candles used",   str(ind["candles"]))

    with col_fund:
        st.markdown("#### 📋 Fundamentals")
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

        indicator_row("P/E Ratio",      f"{pe:.1f}" if pe else "—", "High" if pe and pe > 30 else "Moderate" if pe else "")
        indicator_row("EPS",            f"₹{eps:.2f}" if eps else "—")
        indicator_row("Market Cap",     f"₹{mc/1e7:.0f} Cr" if mc else "—")
        indicator_row("Revenue Growth", f"{rg*100:.1f}%" if rg else "—")
        indicator_row("Debt / Equity",  f"{de:.2f}" if de else "—", "High leverage" if de and de > 1 else "")
        indicator_row("ROE",            f"{roe*100:.1f}%" if roe else "—", "Strong" if roe and roe > 0.15 else "")
        indicator_row("Dividend Yield", f"{dy*100:.2f}%" if dy else "—")
        indicator_row("Book Value",     f"₹{bv:.2f}" if bv else "—")
        indicator_row("Price/Book",     f"{pb:.2f}x" if pb else "—")
        indicator_row("Current Ratio",  f"{cr:.2f}" if cr else "—")
        indicator_row("Profit Margin",  f"{pm*100:.1f}%" if pm else "—")
        indicator_row("Sector",         sec or "—")
        indicator_row("52W High",       fmt_inr(price_data.get("52w_high")))
        indicator_row("52W Low",        fmt_inr(price_data.get("52w_low")))
        indicator_row("Data Source",    price_data["source"])

        if not any([pe, eps, mc, roe, de]):
            st.caption("⚠️ Fundamental data unavailable from Yahoo Finance for this stock. "
                       "This is common for smaller NSE stocks. "
                       f"[View on MoneyControl]({get_news_link(ticker, stock['fullName'])[1]})")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Signal History ────────────────────────────────────────
    st.markdown("### 🕐 Signal History")
    st.caption(f"Session history for **{stock['fullName']}** — last 10 analyses")
    render_signal_history(ticker)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Telegram alert ────────────────────────────────────────
    if curr >= sig["target_price"] * 0.98:
        msg = (f"🎯 Target Alert — {ticker}\n\nCurrent: {fmt_inr(curr)}\n"
               f"Target: {fmt_inr(sig['target_price'])}\nSignal: {signal}\n"
               f"Profit: +{sig['profit_potential']:.1f}%\nProbability: {sig['success_prob']:.0f}%")
        ok  = send_telegram(msg)
        st.success("🎯 Target reached! Telegram alert sent.") if ok else st.warning("Target reached but Telegram alert failed.")

    # ── Disclaimer ────────────────────────────────────────────
    st.markdown(f"""
    <div class="disclaimer">
      ⚠️ Data from {price_data['source']}. Signals are rule-based indicator confluence — <b>not financial advice</b>.
      Always consult a SEBI-registered investment advisor before investing.
      NSE trading hours: Mon–Fri 9:15 AM – 3:30 PM IST.
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

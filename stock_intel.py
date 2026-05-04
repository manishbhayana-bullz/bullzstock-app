#!/usr/bin/env python3
"""
BullzStock Intelligence — v4
Professional fintech dark theme redesign.
All signal logic preserved. UI overhauled for portfolio-grade presentation.
"""

import math
import requests
import streamlit as st
import streamlit.components.v1 as components
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
    page_title="BullzStock Intelligence",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Commented the block of HTML
# with open("pages/bullzstock_professional_ui.html", "r", encoding="utf-8") as f:
#     html = f.read()

# components.html(html, height=1600, scrolling=True)

# ── BullzStock Dark Fintech Theme (locked, not theme-dependent) ──
# st.markdown("""
# <style>
#   /* ── Force dark background on main app area ── */
#   .stApp, .stApp > div { background-color: #0d1117 !important; }
#   section[data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #21262d; }
#   section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
#   .stApp p, .stApp li, .stApp label { color: #c9d1d9 !important; }
#   h1, h2, h3, h4 { color: #e6edf3 !important; }

#   /* ── Metric card ── */
#   .mb-card {
#     background: #161b22;
#     border: 1px solid #21262d;
#     border-radius: 10px;
#     padding: 14px 16px;
#     text-align: center;
#   }
#   .mb-card:hover { border-color: #388bfd44; }
#   .mb-card-label {
#     font-size: 10px;
#     color: #8b949e;
#     font-weight: 700;
#     text-transform: uppercase;
#     letter-spacing: 0.08em;
#     margin-bottom: 4px;
#   }
#   .mb-card-value { font-size: 20px; font-weight: 800; margin: 0; letter-spacing: -0.01em; }
#   .mb-card-sub   { font-size: 11px; color: #8b949e; margin-top: 3px; }

#   /* ── Signal box ── */
#   .signal-box { border-radius: 12px; padding: 20px 24px; margin-bottom: 1rem; }
#   .vote-item  { font-size: 12px; padding: 3px 0; color: #c9d1d9; }

#   /* ── Reasoning box ── */
#   .reasoning-box {
#     border-radius: 10px; padding: 16px 20px; margin: 8px 0;
#     background: #161b22; border: 1px solid #21262d;
#     font-size: 13px; line-height: 1.7; color: #c9d1d9;
#   }

#   /* ── Indicator rows ── */
#   .ind-row {
#     display: flex; justify-content: space-between;
#     padding: 7px 0;
#     border-bottom: 1px solid #21262d;
#     font-size: 12.5px; color: #c9d1d9;
#   }
#   .ind-label { color: #8b949e; font-size: 12px; }

#   /* ── Sidebar stock card ── */
#   .sb-stock-card {
#     background: #161b22; border-radius: 8px;
#     padding: 10px 14px; margin: 8px 0;
#     border-left: 3px solid #238636; font-size: 12px; color: #c9d1d9;
#   }

#   /* ── Visual metric cards ── */
#   .vm-card {
#     border-radius: 10px; padding: 14px 10px 10px;
#     text-align: center;
#     border: 1px solid #21262d; background: #161b22;
#   }
#   .vm-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
#                letter-spacing: 0.07em; color: #8b949e; margin-bottom: 6px; }
#   .vm-value { font-size: 22px; font-weight: 800; margin: 4px 0 2px; letter-spacing: -0.01em; }
#   .vm-sub   { font-size: 11px; color: #8b949e; }

#   /* ── Disclaimer ── */
#   .disclaimer {
#     font-size: 11px; color: #8b949e; margin-top: 1rem;
#     padding: 10px 16px; background: #161b22;
#     border: 1px solid #21262d; border-radius: 8px;
#   }

#   /* ── Streamlit button style override ── */
#   div[data-testid="column"] button {
#     border-radius: 20px !important; font-size: 12px !important;
#     background: #21262d !important; border: 1px solid #30363d !important;
#     color: #c9d1d9 !important;
#   }
#   div[data-testid="column"] button:hover {
#     background: #30363d !important; border-color: #58a6ff !important;
#   }

#   /* ── Section divider ── */
#   .section-label {
#     font-size: 10px; font-weight: 700; text-transform: uppercase;
#     letter-spacing: 0.1em; color: #8b949e; padding: 0 0 8px;
#     border-bottom: 1px solid #21262d; margin-bottom: 12px;
#   }

#   /* ── Price strip ── */
#   .price-strip {
#     background: #161b22; border: 1px solid #21262d;
#     border-radius: 12px; padding: 16px 24px; margin-bottom: 1.2rem;
#     display: flex; align-items: center;
#     justify-content: space-between; flex-wrap: wrap; gap: 10px;
#   }
# </style>
# """, unsafe_allow_html=True) 

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
    "STRONG BUY":  {"color": "#3fb950", "bg": "#0d2b1a", "border": "#238636", "icon": "▲▲"},
    "BUY":         {"color": "#56d364", "bg": "#0a2016", "border": "#2ea043", "icon": "▲"},
    "SHORT SELL":  {"color": "#ff7b72", "bg": "#2d1318", "border": "#da3633", "icon": "▼▼"},
    "SELL":        {"color": "#ffa198", "bg": "#260e10", "border": "#b91c1c", "icon": "▼"},
    "HOLD":        {"color": "#58a6ff", "bg": "#0c1f3d", "border": "#1f6feb", "icon": "▬"},
    "WAIT":        {"color": "#e3b341", "bg": "#2b1d0a", "border": "#9e6a03", "icon": "◌"},
}

# ── Session state ─────────────────────────────────────────────
for key, default in [
    ("signal_history", {}),
    ("chart_show_ema50", True),
    ("chart_show_ema200", True),
    ("chart_show_bb", True),
    ("selected_theme", "Terminator UI"),
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
    
def load_theme_html(theme_name, stock_data=None, signal_data=None, stock_meta=None, timeframe=None):
    theme_map = {
        "Neon UI": "pages/bullzstock_v2.html",
        "Terminator UI": "pages/bullzstock_professional_ui.html"
    }

    file_path = theme_map.get(theme_name)

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    if stock_data and signal_data and stock_meta:
        replacements = {
            "{{TICKER}}": stock_meta["ticker"],
            "{{FULL_NAME}}": stock_meta["fullName"],
            "{{PRICE}}": f"₹{stock_data['current_price']:.2f}",
            "{{CHANGE}}": f"{stock_data['change']:.2f}",
            "{{CHANGE_PCT}}": f"{stock_data['change_pct']:.2f}%",
            "{{OPEN}}": f"₹{stock_data['open']:.2f}",
            "{{HIGH}}": f"₹{stock_data['high']:.2f}",
            "{{LOW}}": f"₹{stock_data['low']:.2f}",
            "{{SIGNAL}}": signal_data["signal"],
            "{{TARGET}}": f"₹{signal_data['target_price']:.2f}",
            "{{STOPLOSS}}": f"₹{signal_data['stop_loss']:.2f}",
            "{{TIMEFRAME}}": timeframe
        }

        for key, value in replacements.items():
            html = html.replace(key, str(value))

    return html

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
        chg_c = "#3fb950" if h.get("change_pct", 0) >= 0 else "#f85149"
        chg_s = "+" if h.get("change_pct", 0) >= 0 else ""
        bg    = "background:#161b22" if i % 2 == 0 else "background:#0d1117"
        rows_html += f"""<tr style="{bg}">
            <td style="padding:7px 10px;font-size:12px;color:#8b949e">{h['time']}</td>
            <td style="padding:7px 10px;font-size:12px;color:#c9d1d9"><b>{h['tf']}</b></td>
            <td style="padding:7px 10px;font-size:12px;color:#c9d1d9">₹{h['price']:,.2f} <span style="color:{chg_c};font-size:11px">({chg_s}{h.get('change_pct',0):.2f}%)</span></td>
            <td style="padding:7px 10px">{badge}</td>
            <td style="padding:7px 10px;font-size:12px;color:{chg_c}">{h.get('regime','—')}</td>
            <td style="padding:7px 10px;font-size:12px;color:#c9d1d9">₹{h.get('target',0):,.2f}</td>
            <td style="padding:7px 10px;font-size:12px;color:#c9d1d9">₹{h.get('stop',0):,.2f}</td>
            <td style="padding:7px 10px;font-size:12px;color:#c9d1d9">{h.get('prob',0):.0f}%</td>
        </tr>"""
    st.markdown(f"""
    <table style="width:100%;border-collapse:collapse;font-size:12px;background:#0d1117;border-radius:10px;overflow:hidden;border:1px solid #21262d">
      <thead><tr style="background:#161b22;border-bottom:1px solid #30363d">
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Time</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">TF</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Price</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Signal</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Regime</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Target</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Stop</th>
        <th style="padding:8px 10px;text-align:left;font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:0.06em">Prob</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

# ── UI Helpers ────────────────────────────────────────────────
def metric_card(label, value, sub=None, value_color="#e6edf3"):
    sub_html = f'<div style="font-size:11px;color:#8b949e;margin-top:3px">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
                padding:14px 16px;text-align:center;margin-bottom:4px">
      <div style="font-size:10px;color:#8b949e;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.08em;margin-bottom:6px">{label}</div>
      <div style="font-size:18px;font-weight:800;color:{value_color};letter-spacing:-0.01em">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)

def indicator_row(label, value, reading="", reading_color="#8b949e"):
    reading_html = f'<span style="color:{reading_color};font-weight:600">{reading}</span>' if reading else ""
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;padding:7px 0;
                border-bottom:1px solid #21262d;font-size:12.5px">
      <span style="color:#8b949e;font-size:12px">{label}</span>
      <span style="color:#c9d1d9">{value} {reading_html}</span>
    </div>""", unsafe_allow_html=True)

# ── TradingView Widget Chart ──────────────────────────────────
def render_tradingview_chart(tv_symbol, tv_interval, show_ema50, show_ema200, show_bb):
    """Replaced TradingView iframe with Plotly — fixes Apple chart caching bug"""
    import yfinance as yf
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd

    # Convert TV symbol back to yfinance format
    ticker_yf = tv_symbol.replace("NSE:", "") + ".NS"
    df = yf.download(ticker_yf, period="6mo", progress=False, auto_adjust=True)

    if df is None or len(df) < 10:
        st.warning(f"Chart data unavailable for {tv_symbol}")
        return

    close  = df["Close"].squeeze()
    high   = df["High"].squeeze()
    low    = df["Low"].squeeze()
    open_  = df["Open"].squeeze()
    volume = df["Volume"].squeeze()
    dates  = df.index

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.75, 0.25])

    fig.add_trace(go.Candlestick(
        x=dates, open=open_, high=high, low=low, close=close,
        name=tv_symbol.replace("NSE:",""),
        increasing_line_color="#26a641", decreasing_line_color="#f85149",
        increasing_fillcolor="#26a641", decreasing_fillcolor="#f85149",
    ), row=1, col=1)

    ema20 = close.ewm(span=20).mean()
    fig.add_trace(go.Scatter(x=dates, y=ema20, name="EMA20",
        line=dict(color="#58a6ff", width=1.5)), row=1, col=1)

    if show_ema50:
        ema50 = close.ewm(span=50).mean()
        fig.add_trace(go.Scatter(x=dates, y=ema50, name="EMA50",
            line=dict(color="#f0883e", width=1.5, dash="dot")), row=1, col=1)

    if show_ema200:
        ema200 = close.ewm(span=200).mean()
        fig.add_trace(go.Scatter(x=dates, y=ema200, name="EMA200",
            line=dict(color="#d29922", width=1.5, dash="dash")), row=1, col=1)

    if show_bb:
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        fig.add_trace(go.Scatter(x=dates, y=sma20+2*std20, name="BB Upper",
            line=dict(color="#8b949e", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=sma20-2*std20, name="BB Lower",
            line=dict(color="#8b949e", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(139,148,158,0.1)"), row=1, col=1)

    colors = ["#26a641" if c >= o else "#f85149" for c, o in zip(close, open_)]
    fig.add_trace(go.Bar(x=dates, y=volume, name="Volume",
        marker_color=colors, opacity=0.7), row=2, col=1)

    fig.update_layout(
        height=530, template="plotly_dark",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        margin=dict(l=10, r=80, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(13,17,23,0.8)", bordercolor="#30363d", borderwidth=1,
                    font=dict(color="#e6edf3", size=12)),
        font=dict(color="#e6edf3"),
        xaxis_rangeslider_visible=False,
        xaxis=dict(gridcolor="#21262d", color="#8b949e"),
        xaxis2=dict(showgrid=False, color="#8b949e"),
        yaxis=dict(gridcolor="#21262d", color="#8b949e"),
        yaxis2=dict(gridcolor="#21262d", color="#8b949e", title=dict(text="Vol", font=dict(color="#8b949e"))),
    )
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker_yf}")

    tv_url = f"https://www.tradingview.com/chart/?symbol={tv_symbol}"
    st.markdown(f'<a href="{tv_url}" target="_blank" style="display:inline-block;margin-top:4px;padding:6px 16px;background:#1c3a5e;color:#58a6ff;border-radius:8px;border:1px solid #58a6ff44;text-decoration:none;font-size:0.85rem;">📊 Open full chart on TradingView →</a>', unsafe_allow_html=True)

# ── Visual Metrics (theme-aware HTML/SVG) ─────────────────────
def render_visual_metrics(rsi_val, prob_val, rr_ratio, closes, period_return):
    rsi_color  = "#f85149" if (rsi_val or 50) > 70 else "#3fb950" if (rsi_val or 50) < 30 else "#e3b341"
    rsi_label  = "Overbought" if (rsi_val or 50) > 70 else "Oversold" if (rsi_val or 50) < 30 else "Neutral"
    rsi_disp   = f"{rsi_val:.1f}" if rsi_val else "—"
    prob_color = "#3fb950" if prob_val >= 65 else "#e3b341" if prob_val >= 45 else "#f85149"
    rr_color   = "#3fb950" if rr_ratio >= 2 else "#e3b341" if rr_ratio >= 1 else "#f85149"
    pr_color   = "#3fb950" if (period_return or 0) >= 0 else "#f85149"
    pr_text    = fmt_pct(period_return) if period_return is not None else "—"

    VM_CARD  = "background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px 10px 12px;text-align:center"
    VM_LABEL = "font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:#8b949e;margin-bottom:6px"
    VM_SUB   = "font-size:11px;color:#8b949e;margin-top:4px"

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
        <div style="{VM_CARD}">
          <div style="{VM_LABEL}">{label}</div>
          <svg viewBox="0 0 120 62" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:130px">
            <path d="M10 52 A50 50 0 0 1 110 52" fill="none" stroke="#21262d" stroke-width="9" stroke-linecap="round"/>
            <path d="M10 52 A50 50 0 {large} 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round"/>
            <line x1="60" y1="52" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
            <circle cx="60" cy="52" r="4" fill="{color}"/>
          </svg>
          <div style="font-size:22px;font-weight:800;color:{color};margin:4px 0 2px;letter-spacing:-0.01em">{disp}</div>
          <div style="{VM_SUB}">{sub}</div>
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
    <div style="{VM_CARD}">
      <div style="{VM_LABEL}">Risk : Reward</div>
      <svg viewBox="0 0 80 76" xmlns="http://www.w3.org/2000/svg" style="width:80px;height:76px;display:block;margin:0 auto">
        <circle cx="40" cy="40" r="28" fill="none" stroke="#f85149" stroke-width="9"
                stroke-dasharray="{rd:.1f} {circ:.1f}" stroke-dashoffset="0" transform="rotate(-90 40 40)"/>
        <circle cx="40" cy="40" r="28" fill="none" stroke="#3fb950" stroke-width="9"
                stroke-dasharray="{rwd:.1f} {circ:.1f}" stroke-dashoffset="{-rd:.1f}" transform="rotate(-90 40 40)"/>
        <text x="40" y="37" text-anchor="middle" font-size="8.5" fill="{rr_color}" font-weight="700" font-family="sans-serif">1:{rr_ratio:.1f}</text>
        <text x="40" y="48" text-anchor="middle" font-size="7" fill="#8b949e" font-family="sans-serif">R:R</text>
      </svg>
      <div style="font-size:16px;font-weight:800;color:{rr_color};margin:4px 0 2px">1 : {rr_ratio:.2f}</div>
      <div style="{VM_SUB}">{'Good ≥2x' if rr_ratio >= 2 else 'Fair 1–2x' if rr_ratio >= 1 else 'Poor <1x'}</div>
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
    <div style="{VM_CARD}">
      <div style="{VM_LABEL}">Period Return</div>
      <div style="padding:4px 6px 0">{spark_svg}</div>
      <div style="font-size:22px;font-weight:800;color:{pr_color};margin:4px 0 2px">{pr_text}</div>
      <div style="{VM_SUB}">{'Positive' if (period_return or 0) >= 0 else 'Negative'} over period</div>
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
    # ── Sidebar ────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 8px 16px;border-bottom:1px solid #21262d;margin-bottom:16px">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="font-size:28px;line-height:1">🐂</div>
            theme_choice = st.selectbox("🎨 Theme",["Terminator UI", "Neon UI"], index=0 if st.session_state.selected_theme == "Terminator UI" else 1) st.session_state.selected_theme = theme_choice
            <div>
              <div style="font-size:16px;font-weight:800;letter-spacing:0.02em;color:#e6edf3;">
                BullzStock
              </div>
              <div style="font-size:10px;color:#8b949e;letter-spacing:0.08em;text-transform:uppercase;">
                NSE India · Signal Engine
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

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
        <div style="background:#161b22;border-radius:8px;padding:10px 14px;margin:8px 0;
                    border-left:3px solid #238636;font-size:12px;color:#c9d1d9">
          <div style="font-weight:700;font-size:13px">{INDUSTRY_ICONS.get(s['industry'],'📌')} {ticker}</div>
          <div style="font-size:12px;margin-top:2px">{s['fullName']}</div>
          <div style="font-size:11px;color:#8b949e;margin-top:4px">
            Industry: {s['industry']}<br>
            Timeframe: {TIMEFRAMES[tf_key]['label']}
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="font-size:11px;color:#8b949e;line-height:1.7">
          <b style="color:#c9d1d9">🕐 NSE Hours</b><br>
          Mon–Fri · 9:15 AM – 3:30 PM IST<br><br>
          <b style="color:#c9d1d9">📡 Data Sources</b><br>
          Yahoo Finance · Alpha Vantage<br><br>
          <b style="color:#c9d1d9">📊 Indicators Used</b><br>
          RSI · MACD · EMA 50/200<br>
          Bollinger Bands · ATR · Stochastic
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑️ Clear Signal History", use_container_width=True):
            st.session_state.signal_history = {}
            st.success("History cleared")

    # ── Header ────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:16px;padding:8px 0 16px;
                border-bottom:1px solid #21262d;margin-bottom:1.2rem">
      <div style="font-size:38px;line-height:1">🐂</div>
      <div>
        <div style="font-size:22px;font-weight:800;color:#e6edf3;line-height:1.1;letter-spacing:-0.01em">
          BullzStock Intelligence
        </div>
        <div style="font-size:11px;color:#8b949e;margin-top:3px;letter-spacing:0.02em">
          NSE India · Rule-Based Signal Engine · ATR Targets · Live Charts
        </div>
      </div>
      <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
        <span style="background:#0d2b1a;color:#3fb950;padding:3px 10px;border-radius:20px;
                     font-size:10px;font-weight:700;border:1px solid #238636;
                     text-transform:uppercase;letter-spacing:0.05em">● Live</span>
        <span style="background:#161b22;color:#8b949e;padding:3px 10px;border-radius:20px;
                     font-size:10px;border:1px solid #21262d">v4</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if not analyse:
        st.markdown("""
        <div style="margin-top:2rem;padding:40px 32px;background:#161b22;border:1px solid #21262d;
                    border-radius:16px;text-align:center">
          <div style="font-size:48px;margin-bottom:12px">🐂</div>
          <div style="font-size:20px;font-weight:700;color:#e6edf3;margin-bottom:8px">
            Select a stock and click Analyse Now
          </div>
          <div style="font-size:13px;color:#8b949e;max-width:480px;margin:0 auto;line-height:1.7">
            BullzStock runs a multi-indicator signal engine across RSI, MACD, EMA 50/200,
            Bollinger Bands, ATR, and Stochastic to generate entry, stop loss, and target levels.
          </div>
          <div style="display:flex;gap:16px;justify-content:center;margin-top:28px;flex-wrap:wrap">
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:14px 20px;text-align:left;min-width:180px">
              <div style="font-size:18px;margin-bottom:6px">🎯</div>
              <div style="font-size:12px;font-weight:700;color:#e6edf3">ATR-Based Targets</div>
              <div style="font-size:11px;color:#8b949e;margin-top:3px">Entry · Target · Stop Loss</div>
            </div>
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:14px 20px;text-align:left;min-width:180px">
              <div style="font-size:18px;margin-bottom:6px">📊</div>
              <div style="font-size:12px;font-weight:700;color:#e6edf3">6-Indicator Confluence</div>
              <div style="font-size:11px;color:#8b949e;margin-top:3px">RSI · MACD · EMA · Bollinger</div>
            </div>
            <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:14px 20px;text-align:left;min-width:180px">
              <div style="font-size:18px;margin-bottom:6px">📈</div>
              <div style="font-size:12px;font-weight:700;color:#e6edf3">Live Plotly Charts</div>
              <div style="font-size:11px;color:#8b949e;margin-top:3px">Candlestick + Volume</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        return

    stock = STOCKS[ticker]
    tf    = TIMEFRAMES[tf_key]

    with st.spinner(f"Fetching {tf['label']} data for {stock['fullName']}..."):
    price_data = fetch_market_data(ticker, tf_key)

    if not price_data:
        st.error("Both Yahoo Finance and Alpha Vantage failed. NSE may be closed (Mon–Fri 9:15–15:30 IST).")
        return

    ind = compute_all(price_data)

    sig = generate_signal(
        price_data["closes"],
        price_data["highs"],
        price_data["lows"],
        price_data["volumes"],
        ind
    )

    selected_html = load_theme_html(
        st.session_state.selected_theme,
        stock_data=price_data,
        signal_data=sig,
        stock_meta={
            "ticker": ticker,
            "fullName": STOCKS[ticker]["fullName"]
        },
        timeframe=tf_key
    )

    components.html(selected_html, height=900, scrolling=True)

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
    chg_color = "#3fb950" if chg_up else "#f85149"
    chg_sym   = "▲" if chg_up else "▼"
    border_col = "#238636" if chg_up else "#da3633"
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid {border_col}33;border-left:3px solid {border_col};
                border-radius:12px;padding:16px 24px;margin-bottom:1.2rem;
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div>
        <div style="font-size:11px;color:#8b949e;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.07em;margin-bottom:4px">
          {INDUSTRY_ICONS.get(stock['industry'],'📌')} {stock['fullName']} · NSE · {tf['label']}
        </div>
        <div style="display:flex;align-items:baseline;gap:10px">
          <span style="font-size:32px;font-weight:800;color:#e6edf3;letter-spacing:-0.02em">₹{curr:,.2f}</span>
          <span style="font-size:15px;color:{chg_color};font-weight:600">{chg_sym} ₹{abs(price_data['change']):.2f} ({abs(price_data['change_pct']):.2f}%)</span>
        </div>
      </div>
      <div style="font-size:11px;color:#8b949e;text-align:right;line-height:1.7">
        <div>{price_data['time']} IST · {price_data['source']}</div>
        <div>Prev close ₹{price_data['prev_close']:,.2f} · {ind['candles']} candles</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # OHLCV
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: metric_card("Open",     fmt_inr(price_data["open"]))
    with c2: metric_card("High",     fmt_inr(price_data["high"]),          value_color="#3fb950")
    with c3: metric_card("Low",      fmt_inr(price_data["low"]),           value_color="#f85149")
    with c4: metric_card("Volume",   f"{price_data['volume']/1e5:.1f}L")
    with c5: metric_card("52W High", fmt_inr(price_data.get("52w_high")), value_color="#3fb950")
    with c6: metric_card("52W Low",  fmt_inr(price_data.get("52w_low")),  value_color="#f85149")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Signal Box + Reasoning ────────────────────────────────
    confluence  = f"{abs(sig['pct_bull']):.0f}% {'bullish' if sig['pct_bull'] >= 0 else 'bearish'} confluence"
    votes_html  = "".join(f'<div style="font-size:12px;padding:3px 0;color:#c9d1d9">· {v}</div>' for v in sig["votes"])
    line1, line2 = build_signal_reasoning(sig, ind, price_data)
    google_link, mc_link = get_news_link(ticker, stock["fullName"])

    st.markdown(f"""
    <div style="border-radius:12px;padding:20px 24px;margin-bottom:1rem;
                background:{sc['bg']};border:1px solid {sc['border']}66;border-left:4px solid {sc['border']}">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px">
        <div>
          <div style="font-size:10px;color:{sc['color']};font-weight:700;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:6px">
            Signal · {tf['label']} · {sig['regime']}
          </div>
          <div style="font-size:28px;font-weight:900;color:{sc['color']};line-height:1;letter-spacing:-0.01em">
            {sc['icon']} {signal}
          </div>
          <div style="font-size:12px;color:{sc['color']}99;margin-top:6px;font-weight:600">{confluence}</div>
        </div>
        <div style="max-width:380px">{votes_html}</div>
      </div>
    </div>
    <div style="border-radius:10px;padding:16px 20px;margin:8px 0;
                background:#161b22;border:1px solid #30363d;
                font-size:13px;line-height:1.7;color:#c9d1d9">
      <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#8b949e;
                  letter-spacing:0.08em;margin-bottom:8px">💡 Signal Reasoning</div>
      <div style="color:#c9d1d9">📌 {line1}</div>
      <div style="margin-top:5px;color:#c9d1d9">📌 {line2}</div>
      <div style="margin-top:10px;font-size:11px;color:#8b949e">
        🔗 News:
        <a href="{google_link}" target="_blank" style="color:#58a6ff;text-decoration:none">Google News</a>
        &nbsp;·&nbsp;
        <a href="{mc_link}" target="_blank" style="color:#58a6ff;text-decoration:none">MoneyControl</a>
        &nbsp;·&nbsp;
        <a href="https://economictimes.indiatimes.com/markets/stocks/news" target="_blank" style="color:#58a6ff;text-decoration:none">Economic Times</a>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Trade Levels ──────────────────────────────────────────
    st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#8b949e;padding:0 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px">🎯 Trade Levels</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Buy / Entry",   fmt_inr(sig["buy_price"]),    value_color="#58a6ff")
    with c2: metric_card("Target Price",  fmt_inr(sig["target_price"]), value_color="#3fb950")
    with c3: metric_card("Stop Loss",     fmt_inr(sig["stop_loss"]),    value_color="#f85149")
    with c4: metric_card("Hold Duration", sig["hold_duration"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Visual Metrics ────────────────────────────────────────
    st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#8b949e;padding:0 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px">📊 Visual Metrics</div>', unsafe_allow_html=True)
    render_visual_metrics(rsi, sig["success_prob"], sig["rr_ratio"],
                          price_data["closes"], ind["period_return"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TradingView Chart ─────────────────────────────────────
    st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#8b949e;padding:0 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px">📈 Live Chart</div>', unsafe_allow_html=True)
    st.caption("Powered by Plotly · Use zoom, pan, and range slider below chart")
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
        st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#8b949e;padding:0 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px">📐 Technical Indicators</div>', unsafe_allow_html=True)
        rsi_val  = f"{rsi:.2f}"           if rsi             else "—"
        macd_val = f"{macd['hist']:.4f}"  if macd["hist"]    else "—"
        boll_val = f"{boll['pct']:.1f}%"  if boll["pct"]     else "—"
        sk_val   = f"{ind['stoch_k']:.1f}%" if ind["stoch_k"] else "—"
        pr       = ind["period_return"]

        rsi_read  = ("Overbought", "#f85149") if rsi and rsi > 70 else ("Oversold", "#3fb950") if rsi and rsi < 30 else ("Neutral", "#8b949e")
        macd_read = ("Bullish ▲", "#3fb950") if macd["hist"] and macd["hist"] > 0 else ("Bearish ▼", "#f85149")
        ema_read  = ("Golden Cross ▲", "#3fb950") if ema50 and ema200 and ema50 > ema200 else ("Death Cross ▼", "#f85149") if ema50 and ema200 else ("N/A", "#8b949e")
        sk_read   = ("Overbought", "#f85149") if ind["stoch_k"] and ind["stoch_k"] > 80 else ("Oversold", "#3fb950") if ind["stoch_k"] and ind["stoch_k"] < 20 else ("Neutral", "#8b949e")

        indicator_row("RSI (14)",       rsi_val,  *rsi_read)
        indicator_row("MACD Histogram", macd_val, *macd_read)
        indicator_row("Bollinger %B",   boll_val, boll["position"])
        indicator_row("EMA 50",         fmt_inr(ema50),  f"Price {'above' if ema50 and curr > ema50 else 'below'} EMA50" if ema50 else "—")
        indicator_row("EMA 200",        fmt_inr(ema200), *ema_read)
        indicator_row("ATR (14)",       fmt_inr(ind["atr"]), "Volatility measure")
        indicator_row("Stochastic K",   sk_val, *sk_read)
        indicator_row("Period Return",  fmt_pct(pr), "▲" if pr and pr >= 0 else "▼", "#3fb950" if pr and pr >= 0 else "#f85149")
        indicator_row("Volume Trend",   ind["volume_trend"])
        indicator_row("Trend",          ind["trend"])
        indicator_row("Candlestick",    ind["pattern"])
        indicator_row("Candles used",   str(ind["candles"]))

    with col_fund:
        st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#8b949e;padding:0 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px">📋 Fundamentals</div>', unsafe_allow_html=True)
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Signal History ────────────────────────────────────────
    st.markdown('<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#8b949e;padding:0 0 8px;border-bottom:1px solid #21262d;margin-bottom:12px">🕐 Signal History · Session</div>', unsafe_allow_html=True)
    st.caption(f"Last 10 analyses for **{stock['fullName']}** this session")
    render_signal_history(ticker)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Disclaimer ────────────────────────────────────────────
    st.markdown(f"""
    <div style="font-size:11px;color:#8b949e;margin-top:1rem;padding:10px 16px;
                background:#161b22;border:1px solid #21262d;border-radius:8px">
      ⚠️ Data from {price_data['source']}. Signals are rule-based indicator confluence —
      <b>not financial advice</b>. Always consult a SEBI-registered investment advisor before investing.
      NSE trading hours: Mon–Fri 9:15 AM – 3:30 PM IST.
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

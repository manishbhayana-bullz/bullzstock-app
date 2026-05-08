#!/usr/bin/env python3
"""
BullzStock Intelligence — v4.0
UI: Dark terminal theme matching bullzstock_v2.html
    Manrope + IBM Plex Mono · Lime #BDFF00 · Surface #0a0b0d
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

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="BullzStock Intelligence",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── V2 Dark Theme CSS ──────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>

<style>
  /* ── Reset Streamlit chrome to dark ── */
  html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #0a0b0d !important;
    color: #e3e2e2 !important;
    font-family: 'Manrope', sans-serif !important;
  }
  [data-testid="stHeader"] { background: transparent !important; }
  [data-testid="stToolbar"] { display: none !important; }
  [data-testid="stDecoration"] { display: none !important; }
  footer { display: none !important; }
  #MainMenu { display: none !important; }

  /* ── Sidebar dark ── */
  [data-testid="stSidebar"] {
    background: #050607 !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
  }
  [data-testid="stSidebar"] * { color: #e3e2e2 !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stRadio label { color: #6b7a94 !important; font-size: 9px !important; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 700; }
  [data-testid="stSidebar"] .stSelectbox > div > div,
  [data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #111315 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    color: #e3e2e2 !important;
    font-family: 'Manrope', sans-serif !important;
    font-size: 12px !important;
  }
  [data-testid="stSidebar"] [data-baseweb="popover"] > div {
    background: #111315 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
  }
  [data-testid="stSidebar"] [role="option"] { background: #111315 !important; color: #e3e2e2 !important; }
  [data-testid="stSidebar"] [role="option"]:hover { background: rgba(189,255,0,0.06) !important; }

  /* Radio buttons */
  [data-testid="stSidebar"] .stRadio > div { gap: 4px !important; }
  [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p { color: #e3e2e2 !important; font-size: 11px !important; }
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child > div {
    background: transparent !important;
    border-color: rgba(255,255,255,0.2) !important;
  }
  [data-testid="stSidebar"] [aria-checked="true"] [data-baseweb="radio"] > div:first-child > div {
    background: #BDFF00 !important;
    border-color: #BDFF00 !important;
  }

  /* Sidebar primary button */
  [data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #b7f700 !important;
    color: #141f00 !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 900 !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px !important;
    box-shadow: 0 4px 20px rgba(183,247,0,0.25) !important;
    transition: all 0.15s !important;
  }
  [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    filter: brightness(1.1) !important;
  }
  [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: #111315 !important;
    color: #6b7a94 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    font-size: 10px !important;
    font-weight: 700 !important;
  }
  [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    color: #e3e2e2 !important;
    border-color: rgba(255,77,106,0.3) !important;
  }

  /* Main content area */
  .block-container {
    background: #0a0b0d !important;
    padding-top: 1rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
  }

  /* ── Typography global ── */
  .mono { font-family: 'IBM Plex Mono', monospace !important; }
  .ms { font-family: 'Material Symbols Outlined'; font-variation-settings: 'FILL' 0, 'wght' 400; font-size: 18px; line-height: 1; vertical-align: middle; }

  /* ── Cards ── */
  .glass-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
  }

  /* ── OHLCV cards ── */
  .ohlcv-card {
    background: #111315;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 12px 14px;
    text-align: center;
  }
  .ohlcv-label {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #6b7a94;
    margin-bottom: 6px;
  }
  .ohlcv-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    font-weight: 600;
    color: #e3e2e2;
  }

  /* ── Signal states ── */
  .signal-wait { background: rgba(245,166,35,0.08); border: 1px solid rgba(245,166,35,0.25); }
  .signal-buy  { background: rgba(189,255,0,0.06);  border: 1px solid rgba(189,255,0,0.25); }
  .signal-sell { background: rgba(255,77,106,0.08); border: 1px solid rgba(255,77,106,0.25); }
  .signal-hold { background: rgba(77,159,255,0.08); border: 1px solid rgba(77,159,255,0.25); }

  /* ── Indicator badges ── */
  .ib { font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 700; letter-spacing: 0.04em; margin-left: 5px; }
  .ib-bull { background: rgba(189,255,0,0.1);  color: #BDFF00; }
  .ib-bear { background: rgba(255,77,106,0.1); color: #ff4d6a; }
  .ib-neut { background: rgba(255,255,255,0.06); color: #8b949e; }
  .ib-warn { background: rgba(245,166,35,0.1); color: #f5a623; }

  /* ── Indicator rows ── */
  .ind-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 11px;
  }
  .ind-row:last-child { border-bottom: none; }
  .ind-label { color: #6b7a94; }

  /* ── Trade level cards ── */
  .trade-card {
    background: #111315;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 14px;
  }
  .trade-label {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #6b7a94;
    margin-bottom: 6px;
  }
  .trade-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 15px;
    font-weight: 700;
  }
  .trade-sub { font-size: 9px; margin-top: 4px; }

  /* ── Sidebar stock card ── */
  .sb-stock-card {
    background: #111315;
    border: 1px solid rgba(189,255,0,0.3);
    border-radius: 8px;
    padding: 12px;
    margin: 6px 0;
    font-size: 12px;
  }

  /* ── Signal history table ── */
  .hist-table { width: 100%; border-collapse: collapse; font-size: 10px; }
  .hist-table th {
    text-align: left;
    padding: 6px 8px;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b7a94;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .hist-table td {
    padding: 7px 8px;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    font-family: 'IBM Plex Mono', monospace;
  }
  .hist-table tr:hover td { background: rgba(255,255,255,0.02); }

  /* ── Section headers ── */
  .section-label {
    font-size: 9px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: #6b7a94;
    margin-bottom: 12px;
  }

  /* ── Pulse animation ── */
  @keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .live-dot { animation: pulse-dot 1.5s infinite; display:inline-block; width:6px; height:6px; border-radius:50%; background:#BDFF00; vertical-align:middle; }

  /* ── Marquee ── */
  @keyframes marquee { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
  .animate-marquee { animation: marquee 25s linear infinite; display:flex; gap:2.5rem; white-space:nowrap; }

  /* ── Streamlit column gaps ── */
  [data-testid="column"] { padding: 0 4px !important; }
  [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }

  /* ── Spinner color ── */
  [data-testid="stSpinner"] { color: #BDFF00 !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #292a2a; border-radius: 10px; }

  /* ── Hide streamlit top padding ── */
  .appview-container .main .block-container { padding-top: 0.5rem; }

  /* ── st.expander dark ── */
  [data-testid="stExpander"] {
    background: #111315 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
  }
  [data-testid="stExpander"] summary { color: #e3e2e2 !important; font-size: 11px !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# ── Config ─────────────────────────────────────────────────────
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
    "BAJAJ-AUTO": {"name": "Bajaj Auto",     "industry": "Automobile", "yf": "BAJAJ-AUTO.NS", "av": "BAJAJ-AUTO", "fullName": "Bajaj Auto Ltd.",         "tv": "NSE:BAJAJ-AUTO"},
    "RELIANCE":   {"name": "Reliance Ind",   "industry": "FMCG",       "yf": "RELIANCE.NS",   "av": "RELIANCE",   "fullName": "Reliance Industries",     "tv": "NSE:RELIANCE"},
}

TIMEFRAMES = {
    "1D": {"label": "1 Day",      "yf_period": "1d",  "yf_interval": "5m",  "av_func": "TIME_SERIES_INTRADAY", "av_interval": "60min", "tv_interval": "5"},
    "1W": {"label": "1 Week",     "yf_period": "5d",  "yf_interval": "1h",  "av_func": "TIME_SERIES_DAILY",    "av_interval": "",       "tv_interval": "60"},
    "1M": {"label": "1 Month",    "yf_period": "1mo", "yf_interval": "1d",  "av_func": "TIME_SERIES_DAILY",    "av_interval": "",       "tv_interval": "D"},
    "6M": {"label": "6 Months",   "yf_period": "6mo", "yf_interval": "1wk", "av_func": "TIME_SERIES_WEEKLY",   "av_interval": "",       "tv_interval": "W"},
    "9M": {"label": "6-9 Months", "yf_period": "9mo", "yf_interval": "1wk", "av_func": "TIME_SERIES_WEEKLY",   "av_interval": "",       "tv_interval": "W"},
}

# signal → (text color, bg class, icon)
SIGNAL_V2 = {
    "STRONG BUY":  {"color": "#BDFF00", "cls": "signal-buy",  "icon": "▲▲", "conf_bg": "rgba(189,255,0,0.12)",  "conf_color": "#BDFF00"},
    "BUY":         {"color": "#BDFF00", "cls": "signal-buy",  "icon": "▲",  "conf_bg": "rgba(189,255,0,0.12)",  "conf_color": "#BDFF00"},
    "SHORT SELL":  {"color": "#ff4d6a", "cls": "signal-sell", "icon": "▼▼", "conf_bg": "rgba(255,77,106,0.12)", "conf_color": "#ff4d6a"},
    "SELL":        {"color": "#ff4d6a", "cls": "signal-sell", "icon": "▼",  "conf_bg": "rgba(255,77,106,0.12)", "conf_color": "#ff4d6a"},
    "HOLD":        {"color": "#4d9fff", "cls": "signal-hold", "icon": "▬",  "conf_bg": "rgba(77,159,255,0.12)", "conf_color": "#4d9fff"},
    "WAIT":        {"color": "#f5a623", "cls": "signal-wait", "icon": "◌",  "conf_bg": "rgba(245,166,35,0.12)", "conf_color": "#f5a623"},
}

# ── Session state ──────────────────────────────────────────────
for key, default in [
    ("signal_history", {}),
    ("chart_show_ema50", True),
    ("chart_show_ema200", True),
    ("chart_show_bb", True),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Helpers ────────────────────────────────────────────────────
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

# ── Technical Indicators ───────────────────────────────────────
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
    position = "Near Upper" if bpct > 80 else "Near Lower" if bpct < 20 else "Mid Range"
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
    if upper_wick > body * 2 and lower_wick < body * 0.3: return "Shooting Star (Bearish)"
    if closes[-1] > closes[-2] > closes[-3] and closes[-1] > opens[-1]: return "Three White Soldiers"
    if closes[-1] < closes[-2] < closes[-3] and closes[-1] < opens[-1]: return "Three Black Crows"
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
        "atr":           calc_atr(h, l, c),
        "stoch_k":       sk,
        "stoch_d":       sd,
        "period_return": ((c[-1]-c[0])/c[0]*100) if len(c) >= 2 else None,
        "trend":         detect_trend(c),
        "pattern":       detect_candlestick(o, h, l, c),
        "volume_trend":  calc_volume_trend(v),
        "candles":       len(c),
    }

# ── Signal Engine ──────────────────────────────────────────────
def generate_signal(closes, highs, lows, volumes, ind):
    rsi    = ind["rsi"];  macd   = ind["macd"]
    boll   = ind["bollinger"]; ema50  = ind["ema50"]
    ema200 = ind["ema200"];    atr    = ind["atr"]
    trend  = ind["trend"];     stoch_k = ind["stoch_k"]
    curr   = closes[-1]
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

def build_signal_reasoning(sig, ind, price_data):
    signal = sig["signal"]
    rsi    = ind["rsi"]
    trend  = ind["trend"]
    votes  = sig["votes"]
    bullish_reasons = [v for v in votes if "Bullish" in v or "Uptrend" in v]
    bearish_reasons = [v for v in votes if "Bearish" in v or "Downtrend" in v]
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
        line2 = f"Price is ranging. RSI at {rsi:.0f} — neutral zone." if rsi else "Waiting for a clearer trend."
    else:
        line1 = "Insufficient directional conviction across indicators."
        line2 = "Consider waiting for RSI breakout or a MACD crossover before entering."
    return line1, line2

def get_news_link(ticker_symbol, full_name):
    encoded = full_name.replace(" ", "+")
    google_news  = f"https://news.google.com/search?q={encoded}+NSE+stock&hl=en-IN&gl=IN"
    moneycontrol = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data={ticker_symbol}&type_search=News"
    return google_news, moneycontrol

# ── Data Fetching ──────────────────────────────────────────────
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

def fetch_market_data(ticker, tf_key):
    tf    = TIMEFRAMES[tf_key]
    stock = STOCKS[ticker]
    data  = fetch_via_yfinance(stock["yf"], tf["yf_period"], tf["yf_interval"])
    return data

def send_telegram(message):
    url = "https://api.telegram.org/bot" + TG_TOKEN + "/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT, "text": message}, timeout=10)
        return r.status_code == 200
    except:
        return False

def update_signal_history(ticker, rec):
    if ticker not in st.session_state.signal_history:
        st.session_state.signal_history[ticker] = []
    h = st.session_state.signal_history[ticker]
    if h and h[-1]["time"] == rec["time"]: h[-1] = rec
    else: h.append(rec)
    st.session_state.signal_history[ticker] = h[-10:]

# ── UI Components ──────────────────────────────────────────────

def ohlcv_card(label, value, color="#e3e2e2"):
    return f"""<div class="ohlcv-card">
      <div class="ohlcv-label">{label}</div>
      <div class="ohlcv-value" style="color:{color}">{value}</div>
    </div>"""

def trade_card(label, value, sub="", value_color="#e3e2e2", sub_color="#6b7a94"):
    return f"""<div class="trade-card">
      <div class="trade-label">{label}</div>
      <div class="trade-value" style="color:{value_color}">{value}</div>
      <div class="trade-sub" style="color:{sub_color}">{sub}</div>
    </div>"""

def indicator_row_v2(label, value, badge_text="", badge_cls="ib-neut"):
    badge = f'<span class="ib {badge_cls}">{badge_text}</span>' if badge_text else ""
    return f"""<div class="ind-row">
      <span class="ind-label">{label}</span>
      <span class="mono" style="color:#e3e2e2">{value}{badge}</span>
    </div>"""

def render_tradingview_chart(tv_symbol, tv_interval):
    widget_html = f"""
    <div style="height:420px;width:100%;border-radius:10px;overflow:hidden;border:1px solid rgba(255,255,255,0.06)">
      <div id="tv_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "{tv_interval}",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#0a0b0d",
        "enable_publishing": false,
        "withdateranges": true,
        "hide_side_toolbar": false,
        "allow_symbol_change": false,
        "save_image": false,
        "container_id": "tv_chart",
        "hide_top_toolbar": false,
        "hide_legend": false,
        "show_popup_button": true,
        "popup_width": "1000",
        "popup_height": "650",
        "backgroundColor": "rgba(10,11,13,1)",
        "gridColor": "rgba(255,255,255,0.04)"
      }});
      </script>
    </div>"""
    st.components.v1.html(widget_html, height=430, scrolling=False)

def render_visual_metrics(rsi_val, prob_val, rr_ratio, closes, period_return):
    rsi_color  = "#ff4d6a" if (rsi_val or 50) > 70 else "#BDFF00" if (rsi_val or 50) < 30 else "#f5a623"
    rsi_label  = "Overbought" if (rsi_val or 50) > 70 else "Oversold" if (rsi_val or 50) < 30 else "Neutral"
    rsi_disp   = f"{rsi_val:.1f}" if rsi_val else "—"
    prob_color = "#BDFF00" if prob_val >= 65 else "#f5a623" if prob_val >= 45 else "#ff4d6a"
    rr_color   = "#BDFF00" if rr_ratio >= 2 else "#f5a623" if rr_ratio >= 1 else "#ff4d6a"
    pr_color   = "#BDFF00" if (period_return or 0) >= 0 else "#ff4d6a"
    pr_text    = fmt_pct(period_return) if period_return is not None else "—"

    def gauge_svg(val, max_val, color, disp, sub):
        pct   = min(val / max_val, 1.0)
        angle = pct * 180 - 180
        rad   = math.radians(angle)
        nx    = 40 + 26 * math.cos(rad)
        ny    = 40 + 26 * math.sin(rad)
        ex    = 8 + (64) * pct
        large = 1 if pct > 0.5 else 0
        ex2   = 8 + 32 * math.cos(math.radians(pct * 180 - 180)) + 32
        ey2   = 40 + 32 * math.sin(math.radians(pct * 180 - 180))
        return f"""
        <svg viewBox="0 0 80 44" style="width:65px;margin:0 auto;display:block">
          <path d="M8 40 A32 32 0 0 1 72 40" fill="none" stroke="#1e2022" stroke-width="7" stroke-linecap="round"/>
          <path d="M8 40 A32 32 0 {large} 1 {ex2:.1f} {ey2:.1f}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/>
          <line x1="40" y1="40" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
          <circle cx="40" cy="40" r="3" fill="{color}"/>
        </svg>
        <p style="font-family:'IBM Plex Mono',monospace;font-size:15px;font-weight:900;color:{color};text-align:center;margin:2px 0">{disp}</p>
        <p style="font-size:9px;color:#6b7a94;text-align:center">{sub}</p>"""

    rsi_svg  = gauge_svg(rsi_val or 50, 100, rsi_color, rsi_disp, rsi_label)
    prob_svg = gauge_svg(prob_val, 100, prob_color, f"{prob_val:.0f}%",
                         "High confidence" if prob_val >= 65 else "Moderate" if prob_val >= 45 else "Low confidence")

    total = 1 + max(rr_ratio, 0.01)
    circ  = 2 * math.pi * 20
    rd    = (1 / total) * circ
    rwd   = (max(rr_ratio, 0.01) / total) * circ
    rr_svg = f"""
    <svg viewBox="0 0 56 56" style="width:48px;margin:4px auto 0;display:block">
      <circle cx="28" cy="28" r="20" fill="none" stroke="#ff4d6a" stroke-width="7"
              stroke-dasharray="{rd:.1f} {circ:.1f}" stroke-dashoffset="0" transform="rotate(-90 28 28)"/>
      <circle cx="28" cy="28" r="20" fill="none" stroke="#BDFF00" stroke-width="7"
              stroke-dasharray="{rwd:.1f} {circ:.1f}" stroke-dashoffset="{-rd:.1f}" transform="rotate(-90 28 28)"/>
      <text x="28" y="25" text-anchor="middle" font-family="IBM Plex Mono" font-size="6" fill="#e3e2e2" font-weight="700">1:{rr_ratio:.1f}</text>
      <text x="28" y="34" text-anchor="middle" font-family="IBM Plex Mono" font-size="5.5" fill="#6b7a94">R:R</text>
    </svg>
    <p style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:900;color:{rr_color};text-align:center;margin:4px 0">1 : {rr_ratio:.2f}</p>
    <p style="font-size:9px;color:#6b7a94;text-align:center">{'Good ≥2x' if rr_ratio >= 2 else 'Fair 1–2x' if rr_ratio >= 1 else 'Poor <1x'}</p>"""

    # Sparkline
    spark_svg = ""
    if closes and len(closes) > 1:
        mn, mx = min(closes), max(closes)
        rng    = mx - mn if mx != mn else 1
        w, h   = 70, 34
        pts    = [f"{int(i/(len(closes)-1)*w)},{int(h-((c-mn)/rng)*h)}" for i, c in enumerate(closes)]
        spark_svg = f"""<svg viewBox="0 0 {w} {h}" style="width:65px;height:34px;display:block;margin:4px auto 0">
          <polyline points="{' '.join(pts)}" fill="none" stroke="{pr_color}" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>"""

    spark_html = f"""{spark_svg}
    <p style="font-family:'IBM Plex Mono',monospace;font-size:15px;font-weight:900;color:{pr_color};text-align:center;margin:2px 0">{pr_text}</p>
    <p style="font-size:9px;color:#6b7a94;text-align:center">{'Positive' if (period_return or 0) >= 0 else 'Negative'} period</p>"""

    card_style = "background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px;text-align:center"
    label_style = "font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.12em;font-weight:700;margin-bottom:4px"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div style="{card_style}"><p style="{label_style}">RSI (14)</p>{rsi_svg}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div style="{card_style}"><p style="{label_style}">Success Prob.</p>{prob_svg}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div style="{card_style}"><p style="{label_style}">Risk : Reward</p>{rr_svg}</div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div style="{card_style}"><p style="{label_style}">Period Return</p>{spark_html}</div>', unsafe_allow_html=True)

def render_signal_history(ticker):
    history = st.session_state.signal_history.get(ticker, [])
    if not history:
        st.markdown('<p style="font-size:11px;color:#6b7a94;padding:12px 0">No history yet — run Analyse to build it.</p>', unsafe_allow_html=True)
        return

    sig_colors = {
        "STRONG BUY": ("#BDFF00", "ib-bull"), "BUY": ("#BDFF00", "ib-bull"),
        "SHORT SELL": ("#ff4d6a", "ib-bear"), "SELL": ("#ff4d6a", "ib-bear"),
        "HOLD": ("#4d9fff", "ib-neut"), "WAIT": ("#f5a623", "ib-warn"),
    }
    rows = ""
    for h in reversed(history):
        sig = h["signal"]
        sc  = sig_colors.get(sig, ("#6b7a94", "ib-neut"))
        chg_c = "#BDFF00" if h.get("change_pct", 0) >= 0 else "#ff4d6a"
        chg_s = "+" if h.get("change_pct", 0) >= 0 else ""
        rows += f"""<tr>
          <td style="color:#6b7a94">{h['time']}</td>
          <td style="font-weight:700">{h['tf']}</td>
          <td>₹{h['price']:,.2f} <span style="color:{chg_c};font-size:9px">({chg_s}{h.get('change_pct',0):.2f}%)</span></td>
          <td><span class="ib {sc[1]}" style="font-size:9px;padding:3px 7px">{h['signal']}</span></td>
          <td style="color:#6b7a94">{h.get('regime','—')}</td>
          <td style="color:#BDFF00">₹{h.get('target',0):,.2f}</td>
          <td style="color:#ff4d6a">₹{h.get('stop',0):,.2f}</td>
          <td>{h.get('prob',0):.0f}%</td>
        </tr>"""

    st.markdown(f"""
    <table class="hist-table">
      <thead><tr>
        <th>Time</th><th>TF</th><th>Price</th><th>Signal</th>
        <th>Regime</th><th>Target</th><th>Stop</th><th>Prob</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

# ── Main ───────────────────────────────────────────────────────
def main():

    # ── Sidebar ────────────────────────────────────────────────
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="padding:16px 4px 20px;border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:12px">
          <div style="display:flex;align-items:center;gap:12px">
            <div style="width:40px;height:40px;border-radius:10px;background:#b7f700;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">🐂</div>
            <div>
              <div style="font-size:18px;font-weight:900;color:#a3e635;letter-spacing:-0.02em;font-family:'Manrope',sans-serif">BullzStock</div>
              <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.18em;color:#4b5563;margin-top:2px">NSE India · Signal Engine</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Nav (visual only — Streamlit handles routing)
        st.markdown("""
        <div style="margin-bottom:16px">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#4b5563;padding:0 4px;margin-bottom:6px">Navigation</div>
          <div style="background:#1c1d1f;border-left:2px solid #a3e635;padding:8px 12px;border-radius:6px;margin-bottom:2px;display:flex;align-items:center;gap:8px">
            <span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#a3e635">📈 Stock Intel</span>
          </div>
          <a href="/2_Screener" style="text-decoration:none">
            <div style="padding:8px 12px;border-radius:6px;margin-bottom:2px;display:flex;align-items:center;gap:8px;cursor:pointer">
              <span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#4b5563">🔍 Screener</span>
            </div>
          </a>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#4b5563;margin-bottom:6px">Filter by Industry</div>', unsafe_allow_html=True)
        industries = ["All"] + sorted(set(v["industry"] for v in STOCKS.values()))
        chosen_ind = st.selectbox("Industry", industries,
                                  format_func=lambda x: f"{INDUSTRY_ICONS.get(x,'📌')} {x}",
                                  label_visibility="collapsed")

        filtered       = {k: v for k, v in STOCKS.items() if chosen_ind == "All" or v["industry"] == chosen_ind}
        ticker_options = list(filtered.keys())
        ticker_labels  = [f"{t} — {filtered[t]['name']}" for t in ticker_options]

        st.markdown('<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#4b5563;margin:10px 0 6px">Select Stock</div>', unsafe_allow_html=True)
        ticker_idx = st.selectbox("Stock", range(len(ticker_options)),
                                  format_func=lambda i: ticker_labels[i],
                                  label_visibility="collapsed")
        ticker = ticker_options[ticker_idx]

        st.markdown('<div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#4b5563;margin:10px 0 6px">Timeframe</div>', unsafe_allow_html=True)
        tf_key = st.radio("Timeframe", list(TIMEFRAMES.keys()),
                          format_func=lambda k: TIMEFRAMES[k]["label"],
                          index=2, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        analyse = st.button("⚡  Analyse Now", use_container_width=True, type="primary")

        # Selected stock card
        s = STOCKS[ticker]
        st.markdown(f"""
        <div class="sb-stock-card" style="margin-top:12px">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <div>
              <div style="font-weight:900;font-size:13px;color:#e3e2e2">{ticker}</div>
              <div style="font-size:10px;color:#6b7a94;margin-top:2px">{s['fullName']}</div>
            </div>
            <div style="font-size:9px;font-weight:700;background:rgba(189,255,0,0.1);color:#BDFF00;padding:2px 8px;border-radius:20px">
              {s['industry']}
            </div>
          </div>
          <div style="margin-top:8px;font-size:10px;color:#6b7a94">
            TF: <span style="color:#e3e2e2;font-weight:700">{TIMEFRAMES[tf_key]['label']}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        # NSE info
        st.markdown("""
        <div style="margin-top:16px;padding:12px;background:#111315;border:1px solid rgba(255,255,255,0.04);border-radius:8px">
          <div style="font-size:9px;color:#6b7a94;line-height:1.9">
            <div style="font-weight:700;color:#e3e2e2;margin-bottom:4px">🕐 NSE Hours</div>
            Mon–Fri · 9:15 AM – 3:30 PM IST
            <div style="font-weight:700;color:#e3e2e2;margin:8px 0 4px">📡 Data Sources</div>
            Yahoo Finance · Alpha Vantage
            <div style="font-weight:700;color:#e3e2e2;margin:8px 0 4px">📐 Indicators</div>
            RSI · MACD · EMA 50/200<br>
            Bollinger · ATR · Stochastic
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear Signal History", use_container_width=True, type="secondary"):
            st.session_state.signal_history = {}
            st.success("History cleared")

    # ── Top header bar ─────────────────────────────────────────
    st.markdown("""
    <div style="background:#050607;border:1px solid rgba(255,255,255,0.05);border-radius:12px;
                padding:12px 20px;margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div style="display:flex;align-items:center;gap:16px">
        <div style="display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.03);
                    border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:6px 12px">
          <span class="live-dot"></span>
          <span style="font-size:12px;font-weight:900;color:#a3e635;font-family:'Manrope',sans-serif">BullzStock</span>
          <span style="font-size:10px;color:#6b7a94">NSE Intelligence</span>
        </div>
        <span style="font-size:10px;color:#4b5563;font-family:'IBM Plex Mono',monospace">v4.0-STABLE</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <div>
          <div style="font-size:8px;text-transform:uppercase;letter-spacing:0.15em;color:#4b5563;font-weight:700">Market Status</div>
          <div style="display:flex;align-items:center;gap:6px;margin-top:2px">
            <span class="live-dot"></span>
            <span style="font-size:10px;font-weight:700;color:#a3e635">NSE LIVE</span>
          </div>
        </div>
        <div style="width:32px;height:32px;border-radius:50%;background:#1c1d1f;border:1px solid rgba(163,230,53,0.3);
                    display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;color:#a3e635">MB</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Ticker marquee ─────────────────────────────────────────
    st.markdown("""
    <div style="background:#050607;border:1px solid rgba(255,255,255,0.04);border-radius:8px;
                height:36px;display:flex;align-items:center;overflow:hidden;margin-bottom:16px;padding:0 12px">
      <div style="font-size:9px;font-weight:700;color:#a3e635;flex-shrink:0;margin-right:16px;
                  text-transform:uppercase;letter-spacing:0.1em">⚡ NSE LIVE</div>
      <div style="overflow:hidden;flex:1">
        <div class="animate-marquee" style="font-size:10px;font-weight:700;color:#9ca3af">
          <span>NIFTY 50 <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">22,456.80</span> <span style="color:rgba(163,230,53,0.6)">+0.84%</span></span>
          <span>SENSEX <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">73,852.10</span> <span style="color:rgba(163,230,53,0.6)">+0.76%</span></span>
          <span>BANKNIFTY <span style="font-family:'IBM Plex Mono',monospace;color:#ff4d6a">48,210.50</span> <span style="color:rgba(255,77,106,0.6)">−0.22%</span></span>
          <span>BAJAJ-AUTO <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">9,994.00</span> <span style="color:rgba(163,230,53,0.6)">+4.60%</span></span>
          <span>RELIANCE <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">1,430.80</span> <span style="color:rgba(163,230,53,0.6)">+6.50%</span></span>
          <span>HDFCBANK <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">1,680.20</span> <span style="color:rgba(163,230,53,0.6)">+2.10%</span></span>
          <span>USDINR <span style="font-family:'IBM Plex Mono',monospace;color:#9ca3af">83.42</span> <span style="color:#4b5563">+0.01%</span></span>
          <span>NIFTY 50 <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">22,456.80</span> <span style="color:rgba(163,230,53,0.6)">+0.84%</span></span>
          <span>SENSEX <span style="font-family:'IBM Plex Mono',monospace;color:#a3e635">73,852.10</span> <span style="color:rgba(163,230,53,0.6)">+0.76%</span></span>
          <span>BANKNIFTY <span style="font-family:'IBM Plex Mono',monospace;color:#ff4d6a">48,210.50</span> <span style="color:rgba(255,77,106,0.6)">−0.22%</span></span>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Welcome state ──────────────────────────────────────────
    if not analyse:
        st.markdown("""
        <div style="background:#111315;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:32px 36px;max-width:700px;margin:20px auto">
          <div style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.18em;color:#4b5563;margin-bottom:16px">📋 How To Use</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
            <div>
              <div style="font-size:13px;font-weight:800;color:#e3e2e2;margin-bottom:12px">Getting Started</div>
              <ol style="font-size:11px;color:#6b7a94;line-height:2;padding-left:18px">
                <li>Select an industry from the sidebar</li>
                <li>Pick a stock from the dropdown</li>
                <li>Choose your timeframe</li>
                <li>Click <strong style="color:#a3e635">⚡ Analyse Now</strong></li>
              </ol>
            </div>
            <div>
              <div style="font-size:13px;font-weight:800;color:#e3e2e2;margin-bottom:12px">Signal Legend</div>
              <div style="font-size:11px;line-height:2.2">
                <div><span style="color:#BDFF00;font-weight:700">▲▲ STRONG BUY</span> <span style="color:#6b7a94">— Strong bullish confluence</span></div>
                <div><span style="color:#BDFF00;font-weight:700">▲ BUY</span> <span style="color:#6b7a94">— Bullish indicators aligned</span></div>
                <div><span style="color:#4d9fff;font-weight:700">▬ HOLD</span> <span style="color:#6b7a94">— Mixed signals, hold position</span></div>
                <div><span style="color:#f5a623;font-weight:700">◌ WAIT</span> <span style="color:#6b7a94">— No clear direction</span></div>
                <div><span style="color:#ff4d6a;font-weight:700">▼ SELL</span> <span style="color:#6b7a94">— Bearish indicators aligned</span></div>
                <div><span style="color:#ff4d6a;font-weight:700">▼▼ SHORT SELL</span> <span style="color:#6b7a94">— Strong bearish confluence</span></div>
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Fetch data ─────────────────────────────────────────────
    stock = STOCKS[ticker]
    tf    = TIMEFRAMES[tf_key]

    with st.spinner(f"Fetching {tf['label']} data for {stock['fullName']}..."):
        price_data = fetch_market_data(ticker, tf_key)

    if not price_data:
        st.markdown("""
        <div style="background:rgba(255,77,106,0.08);border:1px solid rgba(255,77,106,0.25);border-radius:12px;padding:20px;text-align:center">
          <div style="font-size:20px;margin-bottom:8px">⚠️</div>
          <div style="font-weight:700;color:#ff4d6a">Data fetch failed</div>
          <div style="font-size:11px;color:#6b7a94;margin-top:6px">Both Yahoo Finance and Alpha Vantage failed.<br>NSE may be closed (Mon–Fri 9:15–15:30 IST).</div>
        </div>""", unsafe_allow_html=True)
        return

    ind    = compute_all(price_data)
    sig    = generate_signal(price_data["closes"], price_data["highs"],
                             price_data["lows"], price_data["volumes"], ind)
    curr   = price_data["current_price"]
    chg_up = price_data["change"] >= 0
    signal = sig["signal"]
    sv     = SIGNAL_V2.get(signal, SIGNAL_V2["WAIT"])
    macd   = ind["macd"]
    boll   = ind["bollinger"]
    rsi    = ind["rsi"]
    ema50  = ind["ema50"]
    ema200 = ind["ema200"]

    update_signal_history(ticker, {
        "time": datetime.now().strftime("%H:%M:%S"), "tf": tf["label"],
        "price": curr, "change_pct": price_data["change_pct"],
        "signal": signal, "regime": sig["regime"],
        "target": sig["target_price"], "stop": sig["stop_loss"],
        "prob": sig["success_prob"],
    })

    # ── Asset header card ──────────────────────────────────────
    chg_color = "#BDFF00" if chg_up else "#ff4d6a"
    chg_sym   = "▲" if chg_up else "▼"
    chg_arrow = "arrow_drop_up" if chg_up else "arrow_drop_down"

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
                border-radius:14px;padding:20px 24px;margin-bottom:12px;
                display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">
      <div style="display:flex;align-items:center;gap:16px">
        <div style="width:52px;height:52px;border-radius:12px;background:#1c1d1f;border:1px solid rgba(255,255,255,0.08);
                    display:flex;align-items:center;justify-content:center;font-size:22px">
          {INDUSTRY_ICONS.get(stock['industry'],'📊')}
        </div>
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
            <div style="font-size:22px;font-weight:900;color:#e3e2e2;font-family:'Manrope',sans-serif">{ticker}</div>
            <div style="background:#1c1d1f;color:#6b7a94;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em">
              {stock['fullName'].upper()} · NSE
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:34px;font-weight:900;font-family:'IBM Plex Mono',monospace;color:#e3e2e2;line-height:1">₹{curr:,.2f}</div>
            <div style="color:{chg_color};font-weight:700;font-size:15px">{chg_sym} {abs(price_data['change_pct']):.2f}%</div>
          </div>
        </div>
      </div>
      <div style="display:flex;gap:20px;flex-wrap:wrap">
        {ohlcv_card("Open",   fmt_inr(price_data['open']))}
        {ohlcv_card("High",   fmt_inr(price_data['high']),   "#BDFF00")}
        {ohlcv_card("Low",    fmt_inr(price_data['low']),    "#ff4d6a")}
        {ohlcv_card("Volume", f"{price_data['volume']/1e5:.1f}L")}
        {ohlcv_card("52W H",  fmt_inr(price_data.get('52w_high')), "#BDFF00")}
        {ohlcv_card("52W L",  fmt_inr(price_data.get('52w_low')),  "#ff4d6a")}
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Two-column layout: Chart | Signal Panel ────────────────
    col_chart, col_panel = st.columns([2, 1], gap="small")

    with col_chart:
        # Chart TF controls
        tf_btns = ""
        for tfk, tfv in TIMEFRAMES.items():
            active = tfk == tf_key
            cls = "background:rgba(189,255,0,0.1);color:#BDFF00;border:1px solid rgba(189,255,0,0.3)" if active else "background:#111315;color:#6b7a94;border:1px solid rgba(255,255,255,0.06)"
            tf_btns += f'<span style="{cls};font-size:10px;font-weight:700;padding:4px 10px;border-radius:6px;cursor:pointer;font-family:Manrope,sans-serif">{tfk}</span>'

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <div style="display:flex;gap:5px">{tf_btns}</div>
          <div style="width:1px;height:16px;background:rgba(255,255,255,0.08);margin:0 4px"></div>
          <span style="font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;cursor:pointer;
                       {'background:rgba(189,255,0,0.1);color:#BDFF00' if st.session_state.chart_show_ema50 else 'background:#111315;color:#6b7a94'}">EMA 50</span>
          <span style="font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;cursor:pointer;
                       {'background:rgba(245,166,35,0.1);color:#f5a623' if st.session_state.chart_show_ema200 else 'background:#111315;color:#6b7a94'}">EMA 200</span>
          <span style="font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;cursor:pointer;
                       {'background:rgba(77,159,255,0.1);color:#4d9fff' if st.session_state.chart_show_bb else 'background:#111315;color:#6b7a94'}">BB Bands</span>
        </div>""", unsafe_allow_html=True)

        render_tradingview_chart(stock["tv"], tf["tv_interval"])

        # Signal History table
        st.markdown("""
        <div style="margin-top:12px;background:#050607;border:1px solid rgba(255,255,255,0.05);
                    border-radius:10px;padding:14px 16px">
          <div class="section-label">🕐 Signal History · Session</div>""", unsafe_allow_html=True)
        render_signal_history(ticker)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_panel:
        # ── Signal box ─────────────────────────────────────────
        confluence = f"{abs(sig['pct_bull']):.0f}% {'bullish' if sig['pct_bull'] >= 0 else 'bearish'} confluence"
        line1, line2 = build_signal_reasoning(sig, ind, price_data)
        google_link, mc_link = get_news_link(ticker, stock["fullName"])

        # Intensity bar calculation
        pct = sig["pct_bull"]
        n_bars = 5
        filled_bull = round(max(pct, 0) / 100 * n_bars)
        filled_bear = round(max(-pct, 0) / 100 * n_bars)
        intensity_label = ("Strong Buy" if pct >= 60 else "Mild Buy" if pct >= 30
                           else "Strong Sell" if pct <= -60 else "Mild Sell" if pct <= -30
                           else "Weak Bearish" if pct < 0 else "Neutral")
        intensity_color = "#BDFF00" if pct >= 30 else "#ff4d6a" if pct <= -30 else "#f5a623"

        bar_html = ""
        for i in range(n_bars):
            if pct >= 0:
                clr = "rgba(189,255,0,0.6)" if i < filled_bull else "#1e2022"
            else:
                clr = "rgba(255,77,106,0.6)" if i < filled_bear else "#1e2022"
            bar_html += f'<div style="height:5px;flex:1;border-radius:3px;background:{clr}"></div>'

        st.markdown(f"""
        <div style="background:#050607;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:16px">
          <div class="section-label">Signal Analysis</div>

          <!-- Signal pill -->
          <div class="{sv['cls']}" style="border-radius:12px;padding:16px;margin-bottom:12px">
            <div style="display:flex;align-items:start;justify-content:space-between;margin-bottom:10px">
              <div>
                <div style="font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:4px">Signal · {tf['label']}</div>
                <div style="font-size:24px;font-weight:900;color:{sv['color']};font-family:'Manrope',sans-serif">{sv['icon']} {signal}</div>
              </div>
              <span style="font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px;
                           background:{sv['conf_bg']};color:{sv['conf_color']}">{confluence}</span>
            </div>
            <div style="font-size:10px;color:#6b7a94;border-top:1px solid rgba(255,255,255,0.05);padding-top:8px">
              Regime: <span style="font-weight:700;color:{sv['color']}">{sig['regime']}</span>
            </div>
          </div>

          <!-- Trade levels grid -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">
            {trade_card("Entry", fmt_inr(sig['buy_price']), "Buy zone", "#4d9fff")}
            {trade_card("Target", fmt_inr(sig['target_price']), f"+{sig['profit_potential']:.1f}%", "#BDFF00", "#a3e635")}
            {trade_card("Stop Loss", fmt_inr(sig['stop_loss']), f"R:R {sig['rr_ratio']:.2f}x", "#ff4d6a", "#ff4d6a")}
            {trade_card("Hold", sig['hold_duration'], "Duration")}
          </div>

          <!-- Reasoning -->
          <div style="background:#111315;border-left:2px solid {sv['color']};border-top:1px solid rgba(255,255,255,0.04);
                      border-right:1px solid rgba(255,255,255,0.04);border-bottom:1px solid rgba(255,255,255,0.04);
                      border-radius:10px;padding:14px;margin-bottom:12px">
            <div style="font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:0.12em;color:#4b5563;margin-bottom:8px">💡 Signal Reasoning</div>
            <div style="font-size:10px;color:#6b7a94;line-height:1.7">📌 {line1}</div>
            <div style="font-size:10px;color:#6b7a94;line-height:1.7;margin-top:6px">📌 {line2}</div>
            <div style="margin-top:10px;font-size:10px;color:#4b5563">
              🔗
              <a href="{google_link}" target="_blank" style="color:#4d9fff;text-decoration:none;margin:0 4px">Google News</a>·
              <a href="{mc_link}" target="_blank" style="color:#4d9fff;text-decoration:none;margin:0 4px">MoneyControl</a>
            </div>
          </div>

          <!-- Signal intensity bar -->
          <div style="background:#111315;border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:14px">
            <div style="display:flex;justify-content:space-between;font-size:10px;font-weight:700;text-transform:uppercase;color:#4b5563;margin-bottom:10px">
              <span>Signal Intensity</span>
              <span style="color:{intensity_color}">{intensity_label}</span>
            </div>
            <div style="display:flex;gap:4px">{bar_html}</div>
            <div style="display:flex;justify-content:space-between;font-size:9px;color:#4b5563;margin-top:6px">
              <span>Strong Buy</span><span>Strong Sell</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── Visual Metrics (compact for panel) ─────────────────
        st.markdown("""
        <div style="margin-top:8px;background:#050607;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:16px">
          <div class="section-label">Visual Metrics</div>""", unsafe_allow_html=True)
        render_visual_metrics(rsi, sig["success_prob"], sig["rr_ratio"],
                              price_data["closes"], ind["period_return"])
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Technical Indicators ────────────────────────────────
        rsi_val  = f"{rsi:.2f}"           if rsi             else "—"
        macd_val = f"{macd['hist']:.4f}"  if macd["hist"]    else "—"
        boll_val = f"{boll['pct']:.1f}%"  if boll["pct"]     else "—"
        sk_val   = f"{ind['stoch_k']:.1f}%" if ind["stoch_k"] else "—"
        pr       = ind["period_return"]

        rsi_badge  = ("Overbought", "ib-bear") if rsi and rsi > 70 else ("Oversold", "ib-bull") if rsi and rsi < 30 else ("Neutral", "ib-neut")
        macd_badge = ("Bullish ▲", "ib-bull") if macd["hist"] and macd["hist"] > 0 else ("Bearish ▼", "ib-bear")
        ema_badge  = ("Golden Cross ▲", "ib-bull") if ema50 and ema200 and ema50 > ema200 else ("Death Cross ▼", "ib-bear") if ema50 and ema200 else ("N/A", "ib-neut")
        boll_badge = ("Near Upper", "ib-bear") if boll["pct"] and boll["pct"] > 80 else ("Near Lower", "ib-bull") if boll["pct"] and boll["pct"] < 20 else ("Mid Range", "ib-neut")
        sk_badge   = ("Overbought", "ib-bear") if ind["stoch_k"] and ind["stoch_k"] > 80 else ("Oversold", "ib-bull") if ind["stoch_k"] and ind["stoch_k"] < 20 else ("Neutral", "ib-neut")

        st.markdown(f"""
        <div style="margin-top:8px;background:#050607;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:16px">
          <div class="section-label">📐 Technical Indicators</div>
          {indicator_row_v2("RSI (14)", rsi_val, *rsi_badge)}
          {indicator_row_v2("MACD Histogram", macd_val, *macd_badge)}
          {indicator_row_v2("Bollinger %B", boll_val, *boll_badge)}
          {indicator_row_v2("EMA 50", fmt_inr(ema50), *ema_badge)}
          {indicator_row_v2("EMA 200", fmt_inr(ema200))}
          {indicator_row_v2("ATR (14)", fmt_inr(ind['atr']), "Volatility", "ib-neut")}
          {indicator_row_v2("Stochastic K", sk_val, *sk_badge)}
          {indicator_row_v2("Period Return", fmt_pct(pr), ("▲ Positive" if pr and pr >= 0 else "▼ Negative") if pr else "", "ib-bull" if pr and pr >= 0 else "ib-bear")}
          {indicator_row_v2("Volume Trend", ind['volume_trend'])}
          {indicator_row_v2("Trend", ind['trend'])}
          {indicator_row_v2("Candlestick", ind['pattern'])}
          {indicator_row_v2("Candles Used", str(ind['candles']))}
        </div>""", unsafe_allow_html=True)

        # ── Fundamentals ────────────────────────────────────────
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

        no_fund = not any([pe, eps, mc, roe, de])
        fund_note = f"""<div style="font-size:10px;color:#f5a623;padding:8px;background:rgba(245,166,35,0.06);border-radius:6px;margin-top:8px">
          ⚠ Fundamental data unavailable from Yahoo Finance for this ticker.
          <a href="{mc_link}" target="_blank" style="color:#4d9fff;text-decoration:none">View on MoneyControl →</a>
        </div>""" if no_fund else ""

        st.markdown(f"""
        <div style="margin-top:8px;background:#050607;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:16px">
          <div class="section-label">📋 Fundamentals</div>
          {indicator_row_v2("P/E Ratio",      f"{pe:.1f}" if pe else "—", "High" if pe and pe > 30 else "Fair", "ib-warn" if pe and pe > 30 else "ib-neut")}
          {indicator_row_v2("EPS",            f"₹{eps:.2f}" if eps else "—")}
          {indicator_row_v2("Market Cap",     f"₹{mc/1e7:.0f} Cr" if mc else "—")}
          {indicator_row_v2("Revenue Growth", f"{rg*100:.1f}%" if rg else "—", ("Positive" if rg and rg > 0 else "Negative") if rg else "", "ib-bull" if rg and rg > 0 else "ib-bear" if rg else "ib-neut")}
          {indicator_row_v2("Debt / Equity",  f"{de:.2f}" if de else "—", "High leverage" if de and de > 1 else "", "ib-warn" if de and de > 1 else "ib-neut")}
          {indicator_row_v2("ROE",            f"{roe*100:.1f}%" if roe else "—", "Strong" if roe and roe > 0.15 else "", "ib-bull" if roe and roe > 0.15 else "ib-neut")}
          {indicator_row_v2("Dividend Yield", f"{dy*100:.2f}%" if dy else "—")}
          {indicator_row_v2("Book Value",     f"₹{bv:.2f}" if bv else "—")}
          {indicator_row_v2("Price/Book",     f"{pb:.2f}x" if pb else "—")}
          {indicator_row_v2("Profit Margin",  f"{pm*100:.1f}%" if pm else "—")}
          {indicator_row_v2("Sector",         sec or "—")}
          {indicator_row_v2("Data Source",    price_data['source'])}
          {fund_note}
        </div>""", unsafe_allow_html=True)

    # ── Footer disclaimer ──────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:16px;background:#050607;border:1px solid rgba(255,255,255,0.04);
                border-radius:10px;padding:12px 16px;display:flex;justify-content:space-between;
                align-items:center;flex-wrap:wrap;gap:8px">
      <div style="font-size:9px;color:#4b5563;line-height:1.8">
        <span class="live-dot" style="margin-right:6px"></span>
        DATA: {price_data['source'].upper()} &nbsp;·&nbsp;
        ENGINE: RULE-BASED · 6 INDICATORS &nbsp;·&nbsp;
        NSE: MON–FRI 9:15 AM – 3:30 PM IST
      </div>
      <div style="font-size:9px;color:#4b5563">
        ⚠ Rule-based signals — <strong style="color:#6b7a94">not financial advice</strong>. Consult a SEBI-registered advisor. &nbsp;·&nbsp; VER: 4.0-STABLE &nbsp;·&nbsp; © BullzStock 2025
      </div>
    </div>""", unsafe_allow_html=True)

    # ── Telegram alert ─────────────────────────────────────────
    if TG_TOKEN and curr >= sig["target_price"] * 0.98:
        msg = (f"🎯 Target Alert — {ticker}\n\nCurrent: {fmt_inr(curr)}\n"
               f"Target: {fmt_inr(sig['target_price'])}\nSignal: {signal}\n"
               f"Profit: +{sig['profit_potential']:.1f}%\nProbability: {sig['success_prob']:.0f}%")
        send_telegram(msg)

if __name__ == "__main__":
    main()

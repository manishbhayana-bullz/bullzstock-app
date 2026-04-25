#!/usr/bin/env python3
"""
============================================================
MB Stock Intelligence — Enhanced Edition
============================================================
Enhancements:
  A. Bloomberg-lite candlestick chart with EMA 50/200, Bollinger Bands,
     volume bars — all in one interactive Plotly chart
     + Gauge charts for RSI and Success Probability
     + Donut chart for Risk:Reward ratio
     + Sparkline for Period Return
  B. Signal history table — last 10 signals per stock (session memory)
  C. Show/Hide toggle buttons for chart indicators

Run with:
    streamlit run MB_Stock_Enhanced.py
============================================================
"""

import math
import json
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

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding: 1rem 2rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .metric-label {
        font-size: 12px;
        color: #6c757d;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 600;
        margin: 0;
    }
    .metric-sub {
        font-size: 11px;
        color: #6c757d;
        margin-top: 2px;
    }
    .signal-box {
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 1rem;
    }
    .vote-item {
        font-size: 13px;
        padding: 3px 0;
        color: #495057;
    }
    .indicator-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 13px;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
    }
    .disclaimer {
        font-size: 11px;
        color: #999;
        margin-top: 1rem;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    .chart-toggle-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 10px 0;
        margin-bottom: 8px;
    }
    .history-table {
        font-size: 12px;
        width: 100%;
        border-collapse: collapse;
    }
    .history-table th {
        background: #f1f3f5;
        padding: 6px 10px;
        text-align: left;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        color: #6c757d;
        border-bottom: 2px solid #dee2e6;
    }
    .history-table td {
        padding: 6px 10px;
        border-bottom: 1px solid #f0f0f0;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Config ────────────────────────────────────────────────────
AV_KEY   = "415951HNPFTK2N7U"
TG_TOKEN = "8726706025:AAF89ngZqHp4-3H1pkIrUaxm5pj_4sNCIxM"
TG_CHAT  = "6946313879"

STOCKS = {
    "PFOCUS":     {"name": "PI Focus",       "industry": "IT",         "yf": "PFOCUS.NS",     "av": "PFOCUS",     "fullName": "Photon Infotech Focus"},
    "HDFCBANK":   {"name": "HDFC Bank",      "industry": "Banking",    "yf": "HDFCBANK.NS",   "av": "HDFCBANK",   "fullName": "HDFC Bank Ltd."},
    "ITC":        {"name": "ITC Ltd.",        "industry": "FMCG",       "yf": "ITC.NS",        "av": "ITC",        "fullName": "ITC Limited"},
    "PNB":        {"name": "PNB",            "industry": "Banking",    "yf": "PNB.NS",        "av": "PNB",        "fullName": "Punjab National Bank"},
    "PAYTM":      {"name": "Paytm",          "industry": "Fintech",    "yf": "PAYTM.NS",      "av": "PAYTM",      "fullName": "One97 Communications"},
    "TATAMOTORS": {"name": "Tata Motors",    "industry": "Automobile", "yf": "TATAMOTORS.NS", "av": "TATAMOTORS", "fullName": "Tata Motors Ltd."},
    "HAL":        {"name": "HAL",            "industry": "Defence",    "yf": "HAL.NS",        "av": "HAL",        "fullName": "Hindustan Aeronautics Ltd."},
    "JUBLFOOD":   {"name": "Jubilant Foods", "industry": "Retail/QSR", "yf": "JUBLFOOD.NS",   "av": "JUBLFOOD",   "fullName": "Jubilant Foodworks Ltd."},
}

TIMEFRAMES = {
    "1D": {"label": "1 Day",      "yf_period": "1d",  "yf_interval": "5m",  "av_func": "TIME_SERIES_INTRADAY", "av_interval": "60min"},
    "1W": {"label": "1 Week",     "yf_period": "5d",  "yf_interval": "1h",  "av_func": "TIME_SERIES_DAILY",    "av_interval": ""},
    "1M": {"label": "1 Month",    "yf_period": "1mo", "yf_interval": "1d",  "av_func": "TIME_SERIES_DAILY",    "av_interval": ""},
    "6M": {"label": "6 Months",   "yf_period": "6mo", "yf_interval": "1wk", "av_func": "TIME_SERIES_WEEKLY",   "av_interval": ""},
    "9M": {"label": "6-9 Months", "yf_period": "9mo", "yf_interval": "1wk", "av_func": "TIME_SERIES_WEEKLY",   "av_interval": ""},
}

SIGNAL_CONFIG = {
    "STRONG BUY":  {"color": "#1a7340", "bg": "#d4edda", "border": "#28a745", "icon": "▲▲"},
    "BUY":         {"color": "#155724", "bg": "#d4edda", "border": "#5cb85c", "icon": "▲"},
    "SHORT SELL":  {"color": "#721c24", "bg": "#f8d7da", "border": "#dc3545", "icon": "▼▼"},
    "SELL":        {"color": "#721c24", "bg": "#f8d7da", "border": "#e06c75", "icon": "▼"},
    "HOLD":        {"color": "#004085", "bg": "#cce5ff", "border": "#007bff", "icon": "▬"},
    "WAIT":        {"color": "#856404", "bg": "#fff3cd", "border": "#ffc107", "icon": "◌"},
}

# ── Session state for signal history & chart toggles ──────────
if "signal_history" not in st.session_state:
    st.session_state.signal_history = {}  # {ticker: [list of signal dicts]}

if "chart_show_ema50"   not in st.session_state: st.session_state.chart_show_ema50   = True
if "chart_show_ema200"  not in st.session_state: st.session_state.chart_show_ema200  = True
if "chart_show_bb"      not in st.session_state: st.session_state.chart_show_bb      = True
if "chart_show_volume"  not in st.session_state: st.session_state.chart_show_volume  = True

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

def pct_color(val):
    if val is None: return "#6c757d"
    return "#1a7340" if float(val) >= 0 else "#721c24"

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
    """Returns full EMA series for chart plotting"""
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
    """Returns Bollinger Band upper/mid/lower series for chart"""
    upper_s, mid_s, lower_s = [], [], []
    for i in range(len(closes)):
        if i < period - 1:
            upper_s.append(None); mid_s.append(None); lower_s.append(None)
        else:
            sl = closes[i - period + 1 : i + 1]
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
    sl = closes[-period:]
    mid = sum(sl) / period
    std = math.sqrt(sum((v - mid)**2 for v in sl) / period)
    upper = mid + 2 * std
    lower = mid - 2 * std
    last = closes[-1]
    bpct = ((last - lower) / (upper - lower) * 100) if (upper - lower) > 0 else 50
    if bpct > 80:   position = "Near Upper (Overbought)"
    elif bpct < 20: position = "Near Lower (Oversold)"
    else:           position = "Mid Range"
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
    mid = len(closes) // 2
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
    if body < rng * 0.1: return "Doji (Indecision / Sideways)"
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
        "rsi":          calc_rsi(c),
        "macd":         calc_macd(c),
        "bollinger":    calc_bollinger(c),
        "ema50":        calc_ema(c, min(50,  len(c))),
        "ema200":       calc_ema(c, min(200, len(c))),
        "ema9":         calc_ema(c, min(9,   len(c))),
        "ema21":        calc_ema(c, min(21,  len(c))),
        "ema50_series": calc_ema_series(c, min(50,  len(c))),
        "ema200_series":calc_ema_series(c, min(200, len(c))),
        "bb_series":    calc_bb_series(c),
        "atr":          calc_atr(h, l, c),
        "stoch_k":      sk,
        "stoch_d":      sd,
        "period_return":((c[-1]-c[0])/c[0]*100) if len(c) >= 2 else None,
        "trend":        detect_trend(c),
        "pattern":      detect_candlestick(o, h, l, c),
        "volume_trend": calc_volume_trend(v),
        "candles":      len(c),
    }

# ── Signal Engine ─────────────────────────────────────────────
def generate_signal(closes, highs, lows, volumes, ind):
    rsi    = ind["rsi"];   macd  = ind["macd"]
    boll   = ind["bollinger"]; ema50 = ind["ema50"]
    ema200 = ind["ema200"];    atr   = ind["atr"]
    trend  = ind["trend"];     stoch_k = ind["stoch_k"]
    curr   = closes[-1]
    score = 0; max_score = 0; votes = []

    max_score += 2
    if rsi is not None:
        if rsi < 30:    score += 2; votes.append(f"RSI {rsi:.1f} — Oversold (Strong Bullish)")
        elif rsi < 45:  score += 1; votes.append(f"RSI {rsi:.1f} — Mildly Oversold (Bullish)")
        elif rsi > 70:  score -= 2; votes.append(f"RSI {rsi:.1f} — Overbought (Strong Bearish)")
        elif rsi > 55:  score -= 1; votes.append(f"RSI {rsi:.1f} — Mildly Overbought (Bearish)")
        else:           votes.append(f"RSI {rsi:.1f} — Neutral")

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
    if "Strong Uptrend" in trend:   score += 2; votes.append("Strong Uptrend confirmed")
    elif "Mild Uptrend" in trend:   score += 1; votes.append("Mild Uptrend")
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

    if "Sideways" in trend or signal in ("HOLD", "WAIT"): regime = "Sideways/Ranging"
    elif signal in ("STRONG BUY", "BUY"):   regime = "Trending Bullish" if "Strong" in trend else "Mild Bullish"
    elif signal in ("SHORT SELL", "SELL"):  regime = "Trending Bearish" if "Strong" in trend else "Mild Bearish"
    else: regime = "Mixed/Volatile"

    if atr is None: atr = curr * 0.015
    atr_target = {"STRONG BUY": 3.0, "BUY": 2.0, "SHORT SELL": 3.0, "SELL": 2.0, "HOLD": 1.5, "WAIT": 1.0}
    atr_sl     = {"STRONG BUY": 1.5, "BUY": 1.2, "SHORT SELL": 1.5, "SELL": 1.2, "HOLD": 1.0, "WAIT": 0.8}

    is_short = signal in ("SHORT SELL", "SELL")
    buy_price    = curr
    target_price = curr - atr * atr_target.get(signal, 2.0) if is_short else curr + atr * atr_target.get(signal, 2.0)
    stop_loss    = curr + atr * atr_sl.get(signal, 1.2)     if is_short else curr - atr * atr_sl.get(signal, 1.2)

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

# ── Data Fetching ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_via_yfinance(yf_ticker, period, interval):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_ticker}?range={period}&interval={interval}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data   = r.json()
            result = data.get("chart", {}).get("result", [None])[0]
            if result:
                meta = result.get("meta", {})
                q    = result.get("indicators", {}).get("quote", [{}])[0]
                timestamps = result.get("timestamp", [])
                opens   = clean_list(q.get("open",   []))
                highs   = clean_list(q.get("high",   []))
                lows    = clean_list(q.get("low",    []))
                closes  = clean_list(q.get("close",  []))
                volumes = clean_list(q.get("volume", []))
                # Convert timestamps to datetime strings for chart
                dates = []
                for ts in timestamps:
                    try:
                        dates.append(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"))
                    except:
                        dates.append("")
                if len(closes) >= 5:
                    curr = meta.get("regularMarketPrice") or closes[-1]
                    prev = meta.get("previousClose") or meta.get("chartPreviousClose") or closes[-2]
                    return {
                        "source": "Yahoo Finance (direct)",
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
                        "dividend_yield": None, "52w_high": meta.get("fiftyTwoWeekHigh"),
                        "52w_low": meta.get("fiftyTwoWeekLow"), "sector": None,
                    }
    except Exception as e:
        st.warning(f"Direct Yahoo error: {e}")

    if not YF_AVAILABLE:
        return None
    try:
        import yfinance as yf
        ticker = yf.Ticker(yf_ticker)
        hist   = ticker.history(period=period, interval=interval, auto_adjust=True)
        if hist.empty or len(hist) < 5:
            return None
        info = {}
        try: info = ticker.info
        except: pass
        opens   = clean_list(hist["Open"].tolist())
        highs   = clean_list(hist["High"].tolist())
        lows    = clean_list(hist["Low"].tolist())
        closes  = clean_list(hist["Close"].tolist())
        volumes = clean_list(hist["Volume"].tolist())
        dates   = [str(d)[:16] for d in hist.index.tolist()]
        curr = closes[-1]; prev = closes[-2] if len(closes) >= 2 else curr
        return {
            "source": "Yahoo Finance (yfinance)",
            "current_price": curr, "prev_close": prev,
            "open": opens[-1] if opens else curr,
            "high": highs[-1] if highs else curr,
            "low":  lows[-1]  if lows  else curr,
            "volume": volumes[-1] if volumes else 0,
            "change": curr - prev,
            "change_pct": ((curr - prev) / prev * 100) if prev else 0,
            "time": datetime.now().strftime("%H:%M"),
            "opens": opens, "highs": highs, "lows": lows,
            "closes": closes, "volumes": volumes,
            "dates": dates,
            "pe_ratio":       info.get("trailingPE"),
            "eps":            info.get("trailingEps"),
            "market_cap":     info.get("marketCap"),
            "revenue_growth": info.get("revenueGrowth"),
            "debt_equity":    info.get("debtToEquity"),
            "roe":            info.get("returnOnEquity"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high":       info.get("fiftyTwoWeekHigh"),
            "52w_low":        info.get("fiftyTwoWeekLow"),
            "sector":         info.get("sector"),
        }
    except Exception as e:
        st.warning(f"yfinance error: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_via_alphavantage(av_symbol, av_func, av_interval):
    url = f"https://www.alphavantage.co/query?function={av_func}&symbol={av_symbol}&apikey={AV_KEY}&outputsize=compact"
    if av_interval: url += f"&interval={av_interval}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
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
            "opens": opens, "highs": highs, "lows": lows, "closes": closes, "volumes": volumes,
            "dates": dates,
            "pe_ratio": None, "eps": None, "market_cap": None, "revenue_growth": None,
            "debt_equity": None, "roe": None, "dividend_yield": None,
            "52w_high": None, "52w_low": None, "sector": None,
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

# ── UI Helpers ────────────────────────────────────────────────
def metric_card(label, value, sub=None, value_color="#212529"):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{value_color}">{value}</div>
        {sub_html}
    </div>""", unsafe_allow_html=True)

def indicator_row(label, value, reading="", reading_color="#212529"):
    reading_html = f'<span style="color:{reading_color};font-weight:500">{reading}</span>' if reading else ""
    st.markdown(f"""
    <div class="indicator-row">
        <span style="color:#6c757d">{label}</span>
        <span>{value} {reading_html}</span>
    </div>""", unsafe_allow_html=True)

# ── FEATURE A: Bloomberg-lite Candlestick Chart ───────────────
def render_candlestick_chart(price_data, ind, sig, ticker_name, tf_label):
    if not PLOTLY_AVAILABLE:
        st.warning("Plotly not installed. Run: pip install plotly")
        return

    opens   = price_data["opens"]
    highs   = price_data["highs"]
    lows    = price_data["lows"]
    closes  = price_data["closes"]
    volumes = price_data["volumes"]
    dates   = price_data.get("dates", list(range(len(closes))))
    curr    = price_data["current_price"]

    ema50_s  = ind.get("ema50_series", [])
    ema200_s = ind.get("ema200_series", [])
    bb_upper, bb_mid, bb_lower = ind.get("bb_series", ([], [], []))

    show_ema50  = st.session_state.chart_show_ema50
    show_ema200 = st.session_state.chart_show_ema200
    show_bb     = st.session_state.chart_show_bb
    show_vol    = st.session_state.chart_show_volume

    # Subplot rows: candles + volume (if shown) in shared subplots
    row_heights = [0.72, 0.28] if show_vol else [1.0]
    rows = 2 if show_vol else 1

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=(None,)
    )

    # ── Candlesticks ──
    candle_colors = {
        "increasing_line_color": "#26a69a",
        "decreasing_line_color": "#ef5350",
        "increasing_fillcolor": "#26a69a",
        "decreasing_fillcolor": "#ef5350",
    }
    fig.add_trace(go.Candlestick(
        x=dates, open=opens, high=highs, low=lows, close=closes,
        name="Price", showlegend=False,
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",  decreasing_fillcolor="#ef5350",
        line=dict(width=1),
    ), row=1, col=1)

    # ── EMA 50 ──
    if show_ema50 and ema50_s:
        fig.add_trace(go.Scatter(
            x=dates, y=ema50_s, mode="lines",
            name="EMA 50", line=dict(color="#f59e0b", width=1.5, dash="solid"),
            opacity=0.9,
        ), row=1, col=1)

    # ── EMA 200 ──
    if show_ema200 and ema200_s:
        fig.add_trace(go.Scatter(
            x=dates, y=ema200_s, mode="lines",
            name="EMA 200", line=dict(color="#8b5cf6", width=1.5, dash="solid"),
            opacity=0.9,
        ), row=1, col=1)

    # ── Bollinger Bands ──
    if show_bb and bb_upper:
        fig.add_trace(go.Scatter(
            x=dates, y=bb_upper, mode="lines",
            name="BB Upper", line=dict(color="#60a5fa", width=1, dash="dash"),
            opacity=0.7,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=bb_mid, mode="lines",
            name="BB Mid", line=dict(color="#93c5fd", width=1, dash="dot"),
            opacity=0.5,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=bb_lower, mode="lines",
            name="BB Lower", line=dict(color="#60a5fa", width=1, dash="dash"),
            opacity=0.7,
            fill="tonexty",
            fillcolor="rgba(96,165,250,0.05)",
        ), row=1, col=1)

    # ── Trade level lines ──
    sig_color_map = {
        "STRONG BUY": "#1a7340", "BUY": "#28a745",
        "SHORT SELL": "#dc3545", "SELL": "#e06c75",
        "HOLD": "#007bff", "WAIT": "#ffc107"
    }
    sig_color = sig_color_map.get(sig["signal"], "#007bff")

    fig.add_hline(y=sig["target_price"], line_dash="dash",
                  line_color="#1a7340", line_width=1.2,
                  annotation_text=f"Target ₹{sig['target_price']:,.0f}",
                  annotation_position="left", row=1, col=1)
    fig.add_hline(y=sig["stop_loss"], line_dash="dash",
                  line_color="#dc3545", line_width=1.2,
                  annotation_text=f"Stop ₹{sig['stop_loss']:,.0f}",
                  annotation_position="left", row=1, col=1)
    fig.add_hline(y=curr, line_dash="dot",
                  line_color=sig_color, line_width=1.5,
                  annotation_text=f"LTP ₹{curr:,.2f}",
                  annotation_position="right", row=1, col=1)

    # ── Volume bars ──
    if show_vol:
        vol_colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(closes, opens)]
        fig.add_trace(go.Bar(
            x=dates, y=volumes,
            name="Volume",
            marker_color=vol_colors,
            marker_line_width=0,
            opacity=0.7,
            showlegend=True,
        ), row=2, col=1)

    # ── Layout ──
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(family="Inter, sans-serif", size=11, color="#c9d1d9"),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            bgcolor="rgba(14,17,23,0.8)",
            bordercolor="#30363d",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        height=520,
        title=dict(
            text=f"<b>{ticker_name}</b>  ·  {tf_label}  ·  {sig['signal']} {SIGNAL_CONFIG.get(sig['signal'], {}).get('icon', '')}",
            font=dict(size=14, color="#e6edf3"),
            x=0.0, xanchor="left",
        ),
        hoverlabel=dict(bgcolor="#161b22", font_size=12, font_color="#e6edf3"),
        hovermode="x unified",
    )

    fig.update_xaxes(
        gridcolor="#21262d", zerolinecolor="#30363d",
        showgrid=True, tickfont=dict(size=10),
    )
    fig.update_yaxes(
        gridcolor="#21262d", zerolinecolor="#30363d",
        showgrid=True, tickformat=",.0f",
        tickprefix="₹", tickfont=dict(size=10),
    )

    if show_vol:
        fig.update_yaxes(tickprefix="", tickformat=".2s", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "displaylogo": False,
    })


# ── FEATURE A: Gauge chart for RSI ───────────────────────────
def render_rsi_gauge(rsi_val):
    if not PLOTLY_AVAILABLE: return
    if rsi_val is None:
        st.markdown("<div style='text-align:center;color:#6c757d;font-size:12px'>RSI: No data</div>", unsafe_allow_html=True)
        return

    color = "#ef5350" if rsi_val > 70 else "#26a69a" if rsi_val < 30 else "#f59e0b"
    label = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Neutral"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rsi_val,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"RSI (14)<br><span style='font-size:11px;color:{color}'>{label}</span>",
               "font": {"size": 13}},
        number={"font": {"size": 22, "color": color}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4a5568",
                     "tickvals": [0, 30, 50, 70, 100], "ticktext": ["0", "30", "50", "70", "100"]},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#1a1f2e",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30],   "color": "rgba(38,166,154,0.15)"},
                {"range": [30, 70],  "color": "rgba(245,158,11,0.08)"},
                {"range": [70, 100], "color": "rgba(239,83,80,0.15)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": rsi_val,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        height=180,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── FEATURE A: Gauge chart for Success Probability ───────────
def render_probability_gauge(prob_val, signal):
    if not PLOTLY_AVAILABLE: return
    color = "#26a69a" if prob_val >= 65 else "#f59e0b" if prob_val >= 45 else "#ef5350"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob_val,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Success Probability", "font": {"size": 13}},
        number={"font": {"size": 22, "color": color}, "suffix": "%"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4a5568",
                     "tickvals": [0, 25, 50, 75, 100]},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#1a1f2e",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40],   "color": "rgba(239,83,80,0.15)"},
                {"range": [40, 65],  "color": "rgba(245,158,11,0.08)"},
                {"range": [65, 100], "color": "rgba(38,166,154,0.15)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": prob_val,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        height=180,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── FEATURE A: Donut chart for Risk:Reward ────────────────────
def render_rr_donut(rr_ratio):
    if not PLOTLY_AVAILABLE: return
    risk = 1
    reward = max(rr_ratio, 0.01)
    color_r = "#ef5350"; color_rw = "#26a69a"
    fig = go.Figure(go.Pie(
        values=[risk, reward],
        labels=["Risk", "Reward"],
        hole=0.62,
        marker=dict(colors=[color_r, color_rw], line=dict(color="#0e1117", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
        showlegend=False,
        direction="clockwise",
        sort=False,
    ))
    fig.add_annotation(
        text=f"1 : {rr_ratio:.1f}",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#e6edf3", family="Inter"),
    )
    fig.update_layout(
        title=dict(text="Risk : Reward", font=dict(size=13), x=0.5, xanchor="center"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", size=11),
        margin=dict(l=10, r=10, t=40, b=10),
        height=180,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── FEATURE A: Sparkline for Period Return ────────────────────
def render_period_sparkline(closes, period_return, tf_label):
    if not PLOTLY_AVAILABLE or not closes: return
    color = "#26a69a" if (period_return or 0) >= 0 else "#ef5350"
    fill_color = "rgba(38,166,154,0.15)" if (period_return or 0) >= 0 else "rgba(239,83,80,0.15)"
    x_idx = list(range(len(closes)))
    fig = go.Figure(go.Scatter(
        x=x_idx, y=closes, mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=fill_color,
        showlegend=False,
        hovertemplate="₹%{y:,.2f}<extra></extra>",
    ))
    pr_text = fmt_pct(period_return) if period_return is not None else "—"
    fig.update_layout(
        title=dict(
            text=f"Period Return  <span style='color:{color}'>{pr_text}</span>",
            font=dict(size=13), x=0, xanchor="left"
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", size=10),
        margin=dict(l=10, r=10, t=40, b=10),
        height=180,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, tickprefix="₹"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── FEATURE B: Signal History ─────────────────────────────────
def update_signal_history(ticker, sig_record):
    if ticker not in st.session_state.signal_history:
        st.session_state.signal_history[ticker] = []
    history = st.session_state.signal_history[ticker]
    # Avoid duplicate entry for same minute
    if history and history[-1]["time"] == sig_record["time"]:
        history[-1] = sig_record  # update in place
    else:
        history.append(sig_record)
    # Keep last 10
    st.session_state.signal_history[ticker] = history[-10:]

def render_signal_history(ticker):
    history = st.session_state.signal_history.get(ticker, [])
    if not history:
        st.caption("No signal history yet for this session. Run Analyse multiple times to build history.")
        return

    rows_html = ""
    for i, h in enumerate(reversed(history)):
        sig    = h["signal"]
        sc     = SIGNAL_CONFIG.get(sig, SIGNAL_CONFIG["HOLD"])
        badge  = f'<span style="background:{sc["bg"]};color:{sc["color"]};border:1px solid {sc["border"]};padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600">{sc["icon"]} {sig}</span>'
        chg_c  = "#26a69a" if h.get("change_pct", 0) >= 0 else "#ef5350"
        chg_s  = "+" if h.get("change_pct", 0) >= 0 else ""
        rows_html += f"""
        <tr style="{'background:#f8f9fa' if i % 2 == 0 else ''}">
            <td>{h['time']}</td>
            <td><b>{h['tf']}</b></td>
            <td>₹{h['price']:,.2f} <span style='color:{chg_c};font-size:11px'>({chg_s}{h.get('change_pct',0):.2f}%)</span></td>
            <td>{badge}</td>
            <td style='color:{chg_c}'>{h.get('regime','—')}</td>
            <td>₹{h.get('target',0):,.2f}</td>
            <td>₹{h.get('stop',0):,.2f}</td>
            <td>{h.get('prob',0):.0f}%</td>
        </tr>"""

    st.markdown(f"""
    <table class="history-table">
        <thead>
            <tr>
                <th>Time</th><th>Timeframe</th><th>Price</th><th>Signal</th>
                <th>Regime</th><th>Target</th><th>Stop Loss</th><th>Probability</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)


# ── FEATURE C: Indicator Toggle Bar ──────────────────────────
def render_chart_toggle_bar():
    st.markdown("**📊 Chart Indicators**")
    c1, c2, c3, c4, _, _, _ = st.columns([1.2, 1.2, 1.5, 1.2, 1, 1, 1])

    with c1:
        ema50_label = "🟡 EMA 50 ✓" if st.session_state.chart_show_ema50 else "🟡 EMA 50"
        if st.button(ema50_label, key="toggle_ema50", use_container_width=True):
            st.session_state.chart_show_ema50 = not st.session_state.chart_show_ema50
            st.rerun()

    with c2:
        ema200_label = "🟣 EMA 200 ✓" if st.session_state.chart_show_ema200 else "🟣 EMA 200"
        if st.button(ema200_label, key="toggle_ema200", use_container_width=True):
            st.session_state.chart_show_ema200 = not st.session_state.chart_show_ema200
            st.rerun()

    with c3:
        bb_label = "🔵 Bollinger Bands ✓" if st.session_state.chart_show_bb else "🔵 Bollinger Bands"
        if st.button(bb_label, key="toggle_bb", use_container_width=True):
            st.session_state.chart_show_bb = not st.session_state.chart_show_bb
            st.rerun()

    with c4:
        vol_label = "📊 Volume ✓" if st.session_state.chart_show_volume else "📊 Volume"
        if st.button(vol_label, key="toggle_vol", use_container_width=True):
            st.session_state.chart_show_volume = not st.session_state.chart_show_volume
            st.rerun()


# ── Main App ──────────────────────────────────────────────────
def main():
    with st.sidebar:
        st.markdown("## 🐂 MB Stock Intelligence")
        st.markdown("*Enhanced Edition — Bloomberg-lite*")
        st.markdown("---")

        industries = ["All"] + sorted(set(v["industry"] for v in STOCKS.values()))
        chosen_ind = st.selectbox("🏭 Industry", industries)

        filtered = {
            k: v for k, v in STOCKS.items()
            if chosen_ind == "All" or v["industry"] == chosen_ind
        }
        ticker_options = list(filtered.keys())
        ticker_labels  = [f"{t} — {filtered[t]['name']}" for t in ticker_options]
        ticker_idx     = st.selectbox("📊 Stock", range(len(ticker_options)), format_func=lambda i: ticker_labels[i])
        ticker         = ticker_options[ticker_idx]

        tf_key = st.radio(
            "⏱ Timeframe",
            list(TIMEFRAMES.keys()),
            format_func=lambda k: TIMEFRAMES[k]["label"],
            index=2,
        )

        analyse = st.button("🔍 Analyse", use_container_width=True, type="primary")

        st.markdown("---")
        st.markdown(f"**Selected:** `{ticker}`")
        st.markdown(f"**Timeframe:** {TIMEFRAMES[tf_key]['label']}")
        st.markdown("---")
        st.markdown("**NSE Hours**")
        st.markdown("Mon–Fri · 9:15 AM – 3:30 PM IST")
        st.markdown("---")
        st.caption("Data: Yahoo Finance + Alpha Vantage")
        st.caption("Signals: RSI · MACD · EMA · Bollinger · ATR · Stochastic")

        # Signal history clear button
        if st.button("🗑️ Clear Signal History", use_container_width=True):
            st.session_state.signal_history = {}
            st.success("History cleared")

    # ── Header ────────────────────────────────────────────────
    st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:0.5rem">
    <div style="font-size:52px;line-height:1">🐂</div>
    <div>
        <div style="font-size:28px;font-weight:700;line-height:1.1">MB Stock Intelligence</div>
        <div style="font-size:13px;color:#6c757d">Live NSE prices · Bloomberg-lite charts · Telegram alerts</div>
    </div>
    <div style="margin-left:auto;background:#1a7340;color:white;padding:4px 14px;
                border-radius:20px;font-size:12px;font-weight:600">MB Enhanced</div>
</div>
<hr style="margin:0.5rem 0 1rem 0">
""", unsafe_allow_html=True)

    if not analyse:
        st.info("👈 Select a stock and timeframe from the sidebar, then click **Analyse**")
        st.markdown("""
        **What's new in Enhanced Edition:**
        - 📈 **Bloomberg-lite chart** — Candlesticks + EMA 50/200 + Bollinger Bands + Volume in one Plotly chart
        - 🎛️ **Show/Hide toggles** — Control which indicators appear on the chart
        - 🔵 **Gauge charts** — RSI and Success Probability as visual dials
        - 🍩 **Donut chart** — Risk:Reward ratio visualised
        - 📉 **Sparkline** — Period return price trace
        - 🕐 **Signal History** — Last 10 signals per stock tracked automatically

        **How the signals work:**
        - Fetches real OHLC data from Yahoo Finance (Alpha Vantage as fallback)
        - Computes RSI, MACD, Bollinger Bands, EMA 50/200, ATR, Stochastic in real time
        - Signal engine weighs all indicators to generate: **STRONG BUY / BUY / SHORT SELL / SELL / HOLD / WAIT**
        - Entry price, target and stop loss are calculated from real ATR (volatility)
        - Telegram alert fires automatically if price reaches target
        """)
        return

    stock = STOCKS[ticker]
    tf    = TIMEFRAMES[tf_key]

    with st.spinner(f"Fetching {tf['label']} data for {stock['fullName']}..."):
        price_data = fetch_market_data(ticker, tf_key)

    if not price_data:
        st.error("Both Yahoo Finance and Alpha Vantage failed. NSE may be closed (Mon–Fri 9:15 AM–3:30 PM IST) or check your internet connection.")
        return

    ind = compute_all(price_data)
    sig = generate_signal(price_data["closes"], price_data["highs"], price_data["lows"], price_data["volumes"], ind)

    curr    = price_data["current_price"]
    chg_up  = price_data["change"] >= 0
    signal  = sig["signal"]
    sc      = SIGNAL_CONFIG.get(signal, SIGNAL_CONFIG["HOLD"])
    macd    = ind["macd"]
    boll    = ind["bollinger"]
    rsi     = ind["rsi"]
    ema50   = ind["ema50"]
    ema200  = ind["ema200"]

    # ── Save to signal history ────────────────────────────────
    now_str = datetime.now().strftime("%H:%M:%S")
    update_signal_history(ticker, {
        "time":       now_str,
        "tf":         tf["label"],
        "price":      curr,
        "change_pct": price_data["change_pct"],
        "signal":     signal,
        "regime":     sig["regime"],
        "target":     sig["target_price"],
        "stop":       sig["stop_loss"],
        "prob":       sig["success_prob"],
    })

    # ── Live price strip ──────────────────────────────────────
    chg_color = "#1a7340" if chg_up else "#721c24"
    chg_sym   = "▲" if chg_up else "▼"
    st.markdown(f"""
    <div style="background:#f8f9fa;border-radius:12px;padding:16px 24px;margin-bottom:1rem;
                border:1px solid #e9ecef;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
            <div style="font-size:13px;color:#6c757d;font-weight:500;text-transform:uppercase;letter-spacing:0.05em">{stock['fullName']} · NSE · {tf['label']}</div>
            <div style="font-size:32px;font-weight:700;margin-top:2px">₹{curr:,.2f}
                <span style="font-size:16px;color:{chg_color};margin-left:8px">{chg_sym} {abs(price_data['change']):.2f} ({abs(price_data['change_pct']):.2f}%)</span>
            </div>
        </div>
        <div style="font-size:12px;color:#6c757d;text-align:right">
            <div>{price_data['time']} IST · {price_data['source']}</div>
            <div>Prev close: ₹{price_data['prev_close']:,.2f} · {ind['candles']} candles</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # OHLV row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card("Open",    fmt_inr(price_data["open"]))
    with c2: metric_card("High",    fmt_inr(price_data["high"]), value_color="#1a7340")
    with c3: metric_card("Low",     fmt_inr(price_data["low"]),  value_color="#721c24")
    with c4: metric_card("Volume",  f"{price_data['volume']/1e5:.1f}L")
    with c5: metric_card("52W High",fmt_inr(price_data.get("52w_high")), value_color="#1a7340")
    with c6: metric_card("52W Low", fmt_inr(price_data.get("52w_low")),  value_color="#721c24")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Signal box ────────────────────────────────────────────
    confluence = f"{abs(sig['pct_bull']):.0f}% {'bullish' if sig['pct_bull'] >= 0 else 'bearish'} confluence"
    votes_html = "".join(f'<div class="vote-item">• {v}</div>' for v in sig["votes"])
    st.markdown(f"""
    <div class="signal-box" style="background:{sc['bg']};border:2px solid {sc['border']}">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
            <div>
                <div style="font-size:12px;color:{sc['color']};font-weight:500;text-transform:uppercase;letter-spacing:0.05em">AI Signal · {tf['label']} · {sig['regime']}</div>
                <div style="font-size:28px;font-weight:700;color:{sc['color']};margin-top:4px">{sc['icon']} {signal}</div>
                <div style="font-size:13px;color:{sc['color']};margin-top:4px">{confluence}</div>
            </div>
            <div style="max-width:420px">{votes_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Trade levels ──────────────────────────────────────────
    st.markdown("### Trade Levels")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Buy / Entry",   fmt_inr(sig["buy_price"]),    value_color="#004085")
    with c2: metric_card("Target Price",  fmt_inr(sig["target_price"]), value_color="#1a7340")
    with c3: metric_card("Stop Loss",     fmt_inr(sig["stop_loss"]),    value_color="#721c24")
    with c4: metric_card("Risk : Reward", f"1 : {sig['rr_ratio']:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── FEATURE A: Mini visual metrics row ────────────────────
    st.markdown("### 📊 Visual Metrics")
    gm1, gm2, gm3, gm4 = st.columns(4)
    with gm1:
        render_rsi_gauge(rsi)
    with gm2:
        render_probability_gauge(sig["success_prob"], signal)
    with gm3:
        render_rr_donut(sig["rr_ratio"])
    with gm4:
        render_period_sparkline(price_data["closes"], ind["period_return"], tf["label"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── FEATURE A+C: Bloomberg-lite Chart with toggles ────────
    st.markdown("### 📈 Bloomberg-lite Chart")
    render_chart_toggle_bar()
    render_candlestick_chart(price_data, ind, sig, stock["fullName"], tf["label"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Indicators + Fundamentals ─────────────────────────────
    col_ind, col_fund = st.columns(2)

    with col_ind:
        st.markdown("#### Technical Indicators")
        rsi_val  = f"{rsi:.2f}"          if rsi              else "—"
        macd_val = f"{macd['hist']:.4f}" if macd["hist"]     else "—"
        boll_val = f"{boll['pct']:.1f}%" if boll["pct"]      else "—"
        sk_val   = f"{ind['stoch_k']:.1f}%" if ind["stoch_k"] else "—"

        rsi_read  = ("Overbought", "#721c24") if rsi and rsi > 70 else ("Oversold", "#1a7340") if rsi and rsi < 30 else ("Neutral", "#495057")
        macd_read = ("Bullish", "#1a7340") if macd["hist"] and macd["hist"] > 0 else ("Bearish", "#721c24")
        if ema50 and ema200:
            ema_read = ("Golden Cross ▲", "#1a7340") if ema50 > ema200 else ("Death Cross ▼", "#721c24")
        else:
            ema_read = ("N/A", "#6c757d")

        sk_read = ("Overbought", "#721c24") if ind["stoch_k"] and ind["stoch_k"] > 80 \
             else ("Oversold", "#1a7340")   if ind["stoch_k"] and ind["stoch_k"] < 20 \
             else ("Neutral", "#495057")

        indicator_row("RSI (14)",        rsi_val,  *rsi_read)
        indicator_row("MACD Histogram",  macd_val, *macd_read)
        indicator_row("Bollinger %B",    boll_val, boll["position"])
        indicator_row("EMA 50",          fmt_inr(ema50),  f"Price {'above' if ema50 and curr > ema50 else 'below'} EMA50" if ema50 else "—")
        indicator_row("EMA 200",         fmt_inr(ema200), *ema_read)
        indicator_row("ATR (14)",        fmt_inr(ind["atr"]), "Volatility")
        indicator_row("Stochastic K",    sk_val, *sk_read)
        pr = ind["period_return"]
        indicator_row("Period Return",   fmt_pct(pr),
                       "▲" if pr and pr >= 0 else "▼",
                       "#1a7340" if pr and pr >= 0 else "#721c24")
        indicator_row("Volume Trend",    ind["volume_trend"])
        indicator_row("Trend",           ind["trend"])
        indicator_row("Candlestick",     ind["pattern"])
        indicator_row("Candles used",    str(ind["candles"]))

    with col_fund:
        st.markdown("#### Fundamentals")
        pe  = price_data.get("pe_ratio")
        eps = price_data.get("eps")
        mc  = price_data.get("market_cap")
        rg  = price_data.get("revenue_growth")
        de  = price_data.get("debt_equity")
        roe = price_data.get("roe")
        dy  = price_data.get("dividend_yield")
        sec = price_data.get("sector")

        indicator_row("P/E Ratio",       f"{pe:.1f}"          if pe  else "—")
        indicator_row("EPS",             f"₹{eps:.2f}"        if eps else "—")
        indicator_row("Market Cap",      f"₹{mc/1e7:.0f} Cr"  if mc  else "—")
        indicator_row("Revenue Growth",  f"{rg*100:.1f}%"     if rg  else "—")
        indicator_row("Debt / Equity",   f"{de:.2f}"          if de  else "—")
        indicator_row("ROE",             f"{roe*100:.1f}%"    if roe else "—")
        indicator_row("Dividend Yield",  f"{dy*100:.2f}%"     if dy  else "—")
        indicator_row("Sector",          sec or "—")
        indicator_row("52W High",        fmt_inr(price_data.get("52w_high")))
        indicator_row("52W Low",         fmt_inr(price_data.get("52w_low")))
        indicator_row("Data Source",     price_data["source"])
        indicator_row("Last Updated",    price_data["time"] + " IST")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── FEATURE B: Signal History Table ──────────────────────
    st.markdown("### 🕐 Signal History — Last 10 Signals")
    st.caption(f"Session history for **{stock['fullName']}** — refreshes each time you click Analyse")
    render_signal_history(ticker)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Telegram alert ────────────────────────────────────────
    if curr >= sig["target_price"] * 0.98:
        msg = (
            f"Target Alert — {ticker}\n\n"
            f"Current: {fmt_inr(curr)}\nTarget: {fmt_inr(sig['target_price'])}\n"
            f"Signal: {signal}\nProfit: +{sig['profit_potential']:.1f}%\n"
            f"Probability: {sig['success_prob']:.0f}%\nRegime: {sig['regime']}"
        )
        ok = send_telegram(msg)
        if ok:
            st.success("🎯 Target reached! Telegram alert sent to your account.")
        else:
            st.warning("Target reached but Telegram alert failed.")

    # ── Disclaimer ────────────────────────────────────────────
    st.markdown(f"""
    <div class="disclaimer">
        Data from {price_data['source']}. Signals based on rule-based indicator confluence — not AI or financial advice.
        Always consult a SEBI-registered advisor before investing. NSE trading hours: Mon–Fri 9:15 AM – 3:30 PM IST.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

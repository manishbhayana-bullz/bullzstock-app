"""
P5 - Top 10 Stock Screener — Clean Rewrite
pages/screener.py

Fixes:
1. Dropdown no longer resets page (session_state architecture)
2. Rationale visible
3. Chart shows correct stock with indicators
4. Better header
5. Green/Yellow/Red score colors
6. MACD legend
"""

import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

# ─── NIFTY 50 ─────────────────────────────────────────────────────────────────
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS",
    "WIPRO.NS", "HCLTECH.NS", "AXISBANK.NS", "KOTAKBANK.NS", "LT.NS",
    "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
    "NESTLEIND.NS", "POWERGRID.NS", "NTPC.NS", "ONGC.NS", "TATACONSUM.NS",
    "TATASTEEL.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "TECHM.NS", "DRREDDY.NS",
    "CIPLA.NS", "EICHERMOT.NS", "GRASIM.NS", "BAJAJFINSV.NS", "COALINDIA.NS",
    "DIVISLAB.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "INDUSINDBK.NS", "M&M.NS",
    "APOLLOHOSP.NS", "BAJAJ-AUTO.NS", "BRITANNIA.NS", "BPCL.NS", "SHREECEM.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "UPL.NS", "ADANIENT.NS",
]

DISPLAY_NAMES = {t: t.replace(".NS", "") for t in NIFTY_50}

STRATEGIES = {
    "Momentum": {
        "label": "Momentum",
        "desc": "Stocks with strong upward price + volume momentum",
        "emoji": "🚀",
        "weights": {"rsi_score": 0.15, "macd_score": 0.25, "volume_score": 0.25, "momentum_score": 0.35},
        "rsi_range": (50, 70),
    },
    "Swing Trade": {
        "label": "Swing Trade",
        "desc": "Oversold stocks with reversal signals — best for 3-10 day trades",
        "emoji": "📊",
        "weights": {"rsi_score": 0.40, "macd_score": 0.30, "volume_score": 0.15, "momentum_score": 0.15},
        "rsi_range": (30, 50),
    },
    "Breakout": {
        "label": "Breakout",
        "desc": "Stocks near 52-week high with volume confirmation",
        "emoji": "💥",
        "weights": {"rsi_score": 0.10, "macd_score": 0.20, "volume_score": 0.35, "momentum_score": 0.35},
        "rsi_range": (60, 80),
    },
    "Value + Trend": {
        "label": "Value + Trend",
        "desc": "Undervalued stocks with positive trend — longer hold 1-3 months",
        "emoji": "🏦",
        "weights": {"rsi_score": 0.30, "macd_score": 0.30, "volume_score": 0.10, "momentum_score": 0.30},
        "rsi_range": (35, 60),
    },
}

# ─── INDICATORS ───────────────────────────────────────────────────────────────

def calc_rsi(series, period=14):
    if len(series) < period + 1:
        return 50.0
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.dropna()
    return float(val.iloc[-1]) if len(val) > 0 else 50.0


def calc_macd_signal(series):
    if len(series) < 35:
        return {"macd": 0, "signal": 0, "hist": 0, "bullish_cross": False}
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    bullish_cross = (
        float(macd.iloc[-1]) > float(signal.iloc[-1]) and
        float(macd.iloc[-2]) <= float(signal.iloc[-2])
    )
    return {"macd": float(macd.iloc[-1]), "signal": float(signal.iloc[-1]),
            "hist": float(hist.iloc[-1]), "bullish_cross": bullish_cross}


def calc_volume_surge(volume):
    if len(volume) < 20:
        return 1.0
    avg_vol = volume.iloc[-21:-1].mean()
    return float(volume.iloc[-1] / avg_vol) if avg_vol > 0 else 1.0


def calc_momentum(close):
    r5  = (close.iloc[-1] / close.iloc[-6]  - 1) * 100 if len(close) >= 6  else 0
    r20 = (close.iloc[-1] / close.iloc[-21] - 1) * 100 if len(close) >= 21 else 0
    r60 = (close.iloc[-1] / close.iloc[-61] - 1) * 100 if len(close) >= 61 else 0
    return {"r5": float(r5), "r20": float(r20), "r60": float(r60)}


def calc_trend(close):
    ema20  = float(close.ewm(span=20).mean().iloc[-1])
    ema50  = float(close.ewm(span=50).mean().iloc[-1]) if len(close) >= 50  else ema20
    ema200 = float(close.ewm(span=200).mean().iloc[-1]) if len(close) >= 200 else ema50
    price  = float(close.iloc[-1])
    score  = sum([price > ema20, price > ema50, price > ema200]) / 3
    label  = "Strong ↑" if score == 1.0 else "Mixed →" if score >= 0.5 else "Weak ↓"
    return {"ema20": ema20, "ema50": ema50, "ema200": ema200,
            "trend_score": score, "trend_label": label}


def calc_atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().dropna()
    return float(atr.iloc[-1]) if len(atr) > 0 else float((high - low).mean())


def normalize(value, min_v, max_v):
    if max_v == min_v:
        return 50.0
    return max(0, min(100, (value - min_v) / (max_v - min_v) * 100))


def score_stock(data, weights, rsi_range):
    rsi = data["rsi"]
    rsi_mid = sum(rsi_range) / 2
    rsi_score = max(0, 100 - abs(rsi - rsi_mid) * 3)

    hist = data["macd"]["hist"]
    macd_score = normalize(hist, -2, 2)
    if data["macd"]["bullish_cross"]:
        macd_score = min(100, macd_score + 20)

    vol_score = normalize(data["volume_surge"], 0.5, 3.0)

    mom = data["momentum"]
    mom_composite = mom["r5"] * 0.3 + mom["r20"] * 0.4 + mom["r60"] * 0.3
    momentum_score = normalize(mom_composite, -10, 20)

    return round(
        rsi_score      * weights["rsi_score"] +
        macd_score     * weights["macd_score"] +
        vol_score      * weights["volume_score"] +
        momentum_score * weights["momentum_score"], 1
    )


# ─── DATA FETCH ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_stocks(tickers):
    results = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
            if df is not None and len(df) > 30:
                results[ticker] = df
        except Exception:
            pass
        time.sleep(0.3)
    return results


def compute_signals(raw_data, strategy_key):
    strategy = STRATEGIES[strategy_key]
    weights  = strategy["weights"]
    rsi_range = strategy["rsi_range"]
    rows = []

    for ticker, df in raw_data.items():
        try:
            close  = df["Close"].squeeze().dropna()
            high   = df["High"].squeeze().dropna()
            volume = df["Volume"].squeeze().dropna()
            if len(close) < 30:
                continue

            rsi        = calc_rsi(close)
            macd       = calc_macd_signal(close)
            vol_surge  = calc_volume_surge(volume)
            momentum   = calc_momentum(close)
            trend      = calc_trend(close)
            price      = float(close.iloc[-1])
            near_high  = price >= float(high.tail(252).max()) * 0.95

            data = {"rsi": rsi, "macd": macd, "volume_surge": vol_surge,
                    "momentum": momentum, "trend": trend}
            sc = score_stock(data, weights, rsi_range)

            rows.append({
                "Ticker":        DISPLAY_NAMES.get(ticker, ticker),
                "Score":         sc,
                "Price":         round(price, 2),
                "RSI":           round(rsi, 1),
                "MACD":          "🟢 Bull Cross" if macd["bullish_cross"] else ("🔵 Bullish" if macd["hist"] > 0 else "🔴 Bearish"),
                "Vol Surge":     f"{vol_surge:.1f}x",
                "5D %":          f"{momentum['r5']:+.1f}%",
                "20D %":         f"{momentum['r20']:+.1f}%",
                "Trend":         trend["trend_label"],
                "Near 52W High": "✅" if near_high else "—",
                "_vol_surge_raw": vol_surge,
                "_r20_raw":      momentum["r20"],
                "_rsi_raw":      rsi,
            })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
    result.index = result.index + 1
    return result


# ─── TRADE SIGNAL ─────────────────────────────────────────────────────────────

def generate_trade_signal(ticker, raw_data, score, strategy_key):
    ticker_ns = ticker + ".NS"
    df = raw_data.get(ticker_ns)
    if df is None or len(df) < 20:
        return None

    close  = df["Close"].squeeze().dropna()
    high   = df["High"].squeeze().dropna()
    low    = df["Low"].squeeze().dropna()
    price  = float(close.iloc[-1])
    atr    = calc_atr(high, low, close)
    rsi    = calc_rsi(close)
    macd   = calc_macd_signal(close)
    trend  = calc_trend(close)
    momentum = calc_momentum(close)

    bullish = 0
    bearish = 0
    rationale = []

    if rsi < 35:
        bullish += 2; rationale.append(f"RSI oversold at {rsi:.1f} — potential reversal zone")
    elif rsi < 50:
        bullish += 1; rationale.append(f"RSI neutral-low at {rsi:.1f} — room to move up")
    elif rsi > 70:
        bearish += 2; rationale.append(f"RSI overbought at {rsi:.1f} — caution on fresh entry")
    elif rsi > 60:
        bullish += 1; rationale.append(f"RSI strong at {rsi:.1f} — momentum intact")

    if macd["bullish_cross"]:
        bullish += 3; rationale.append("MACD bullish crossover just triggered — strongest buy signal")
    elif macd["hist"] > 0:
        bullish += 1; rationale.append("MACD histogram positive — upward momentum continuing")
    else:
        bearish += 2; rationale.append("MACD bearish — wait for crossover before entering")

    if trend["trend_score"] == 1.0:
        bullish += 2; rationale.append("Price above EMA20, EMA50, EMA200 — confirmed uptrend")
    elif trend["trend_score"] >= 0.67:
        bullish += 1; rationale.append("Price above most moving averages — moderate uptrend")
    elif trend["trend_score"] <= 0.33:
        bearish += 2; rationale.append("Price below key moving averages — downtrend caution")

    if momentum["r20"] > 5:
        bullish += 1; rationale.append(f"Strong 20-day momentum: +{momentum['r20']:.1f}%")
    elif momentum["r20"] < -5:
        bearish += 1; rationale.append(f"Weak 20-day momentum: {momentum['r20']:.1f}%")

    net = bullish - bearish
    if net >= 4:
        signal, signal_color, signal_emoji = "BUY", "#40c057", "🟢"
    elif net >= 2:
        signal, signal_color, signal_emoji = "WEAK BUY", "#94d82d", "🟡"
    elif net <= -3:
        signal, signal_color, signal_emoji = "SELL / AVOID", "#ff6b6b", "🔴"
    else:
        signal, signal_color, signal_emoji = "NEUTRAL / WATCH", "#74c0fc", "🔵"

    confidence = "High" if score >= 65 else "Medium" if score >= 45 else "Low"
    conf_color = "#40c057" if confidence == "High" else "#fab005" if confidence == "Medium" else "#ff6b6b"

    ema20 = trend["ema20"]
    if price > ema20 * 1.02:
        entry = round(ema20 * 1.005, 2)
        entry_note = f"Wait for pullback to EMA20 (~₹{entry:,.1f})"
    else:
        entry = round(price, 2)
        entry_note = "Enter at current market price"

    swing_low  = float(low.tail(10).min()) * 0.99
    sl_atr     = round(entry - 1.5 * atr, 2)
    stop_loss  = round(max(sl_atr, swing_low), 2)
    sl_pct     = round((entry - stop_loss) / entry * 100, 2)
    risk       = entry - stop_loss
    target1    = round(entry + risk * 1.5, 2)
    target2    = round(entry + risk * 2.5, 2)
    t1_pct     = round((target1 - entry) / entry * 100, 2)
    t2_pct     = round((target2 - entry) / entry * 100, 2)

    return {
        "signal": signal, "signal_color": signal_color, "signal_emoji": signal_emoji,
        "confidence": confidence, "conf_color": conf_color,
        "entry": entry, "entry_note": entry_note,
        "stop_loss": stop_loss, "sl_pct": sl_pct,
        "target1": target1, "t1_pct": t1_pct,
        "target2": target2, "t2_pct": t2_pct,
        "rsi": round(rsi, 1), "atr": round(atr, 2),
        "trend": trend["trend_label"], "rationale": rationale, "price": price,
    }




# ─── AI COMMENTARY (Google Gemini — Free) ────────────────────────────────────

def get_ai_commentary(ticker, trade, score, strategy_key):
    """
    Call Google Gemini API (free tier) for natural language stock commentary.
    Get free API key: aistudio.google.com → Get API Key (no credit card needed)
    Add to Streamlit secrets: GEMINI_API_KEY = "AIza..."
    """
    import requests
    import streamlit as _st

    prompt = f"""You are a concise stock market analyst for Indian NSE stocks.
Analyze this stock and give a 3-4 line trading commentary.

Stock: {ticker} (NSE India)
Current Price: ₹{trade['price']:,.2f}
Signal: {trade['signal']}
Confidence: {trade['confidence']}
RSI: {trade['rsi']}
Trend: {trade['trend']}
ATR: ₹{trade['atr']:,.2f}
Entry: ₹{trade['entry']:,.1f}
Stop Loss: ₹{trade['stop_loss']:,.1f} (-{trade['sl_pct']}%)
Target 1: ₹{trade['target1']:,.1f} (+{trade['t1_pct']}%)
Target 2: ₹{trade['target2']:,.1f} (+{trade['t2_pct']}%)
Strategy: {strategy_key}
Composite Score: {score}/100
Signal Rationale: {', '.join(trade['rationale'])}

Write exactly 4 sentences:
1. Current technical picture in plain English
2. Key reason for the {trade['signal']} signal
3. Main risk to watch right now
4. One specific actionable sentence for a retail investor

Be direct. Use Indian market context (NSE, Nifty, FII/DII). No disclaimers."""

    try:
        # Read API key from Streamlit secrets
        try:
            api_key = _st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            api_key = ""

        if not api_key or api_key.strip() == "":
            return "__NO_KEY__"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": 300,
                    "temperature": 0.7,
                    "topP": 0.9,
                }
            },
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif response.status_code == 400:
            return f"__ERROR_400__: {response.text[:200]}"
        elif response.status_code == 403:
            return "__ERROR_403__: API key invalid or not enabled for Gemini API"
        elif response.status_code == 429:
            return "__ERROR_429__: Rate limit hit — free tier allows 1500/day"
        else:
            return f"__ERROR_{response.status_code}__: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return "__ERROR_TIMEOUT__"
    except Exception as e:
        return f"__ERROR_EXCEPTION__: {str(e)[:200]}"


def render_trade_panel(ticker, raw_data, score, strategy_key):
    """
    Render trade setup panel.
    Uses Plotly for inline chart (always correct stock, no iframe caching).
    Provides TradingView deep link for full interactive chart.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    trade = generate_trade_signal(ticker, raw_data, score, strategy_key)
    if trade is None:
        st.warning("Not enough data to generate trade setup.")
        return

    ticker_ns = ticker + ".NS"
    df = raw_data.get(ticker_ns)

    # ── HEADER ────────────────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns([3, 3, 2])
    with col_a:
        st.markdown(f"### {ticker}")
        st.caption(
            f"Price: ₹{trade['price']:,.2f}  |  "
            f"ATR(14): ₹{trade['atr']:,.2f}  |  "
            f"RSI: {trade['rsi']}  |  "
            f"Trend: {trade['trend']}"
        )
    with col_b:
        st.markdown(
            f'''<div style="margin-top:10px;">
            <span style="font-size:1.1rem;font-weight:700;
                color:{trade["signal_color"]};
                background:#1a1a2e;
                padding:6px 18px;border-radius:20px;
                border:2px solid {trade["signal_color"]};
                display:inline-block;">
                {trade["signal_emoji"]} {trade["signal"]}
            </span></div>''',
            unsafe_allow_html=True
        )
    with col_c:
        st.markdown(
            f'''<div style="margin-top:14px;text-align:right;">
            <span style="color:{trade["conf_color"]};font-size:0.9rem;
                background:#1a1a2e;padding:4px 12px;border-radius:12px;
                border:1px solid {trade["conf_color"]}88;display:inline-block;">
                Confidence: <strong>{trade["confidence"]}</strong>
            </span></div>''',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── TRADE LEVELS ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📍 Entry", f"₹{trade['entry']:,.1f}", None, help=trade['entry_note'], delta_color="off")
    c2.metric("🛑 Stop Loss", f"₹{trade['stop_loss']:,.1f}", f"-{trade['sl_pct']}% risk",   delta_color="inverse")
    c3.metric("🎯 Target 1",  f"₹{trade['target1']:,.1f}",  f"+{trade['t1_pct']}% (1.5R)", delta_color="normal")
    c4.metric("🚀 Target 2",  f"₹{trade['target2']:,.1f}",  f"+{trade['t2_pct']}% (2.5R)", delta_color="normal")

    st.markdown("")

    # ── RATIONALE ─────────────────────────────────────────────────────────────
    if trade["rationale"]:
        st.markdown("**📋 Signal Rationale:**")
        for r in trade["rationale"]:
            st.markdown(f"- {r}")

    st.markdown("")

    # ── PLOTLY CHART (always correct — reads from raw_data directly) ──────────
    st.markdown(f"**📈 Price Chart — {ticker} (Daily, last 6 months)**")

    if df is not None and len(df) > 10:
        close  = df["Close"].squeeze()
        high   = df["High"].squeeze()
        low    = df["Low"].squeeze()
        open_  = df["Open"].squeeze()
        volume = df["Volume"].squeeze()
        dates  = df.index

        # Calculate EMA lines
        ema20  = close.ewm(span=20).mean()
        ema50  = close.ewm(span=50).mean()

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25]
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=dates, open=open_, high=high, low=low, close=close,
            name=ticker,
            increasing_line_color="#26a641",
            decreasing_line_color="#f85149",
            increasing_fillcolor="#26a641",
            decreasing_fillcolor="#f85149",
        ), row=1, col=1)

        # EMA lines
        fig.add_trace(go.Scatter(
            x=dates, y=ema20, name="EMA20",
            line=dict(color="#58a6ff", width=1.5),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=dates, y=ema50, name="EMA50",
            line=dict(color="#f0883e", width=1.5, dash="dot"),
        ), row=1, col=1)

        # Entry / SL / Target lines
        price_now = float(close.iloc[-1])
        fig.add_hline(y=trade["entry"],     line_color="#58a6ff", line_dash="dash",
                      line_width=1, annotation_text=f"Entry ₹{trade['entry']:,.1f}",
                      annotation_position="right", row=1, col=1)
        fig.add_hline(y=trade["stop_loss"], line_color="#f85149", line_dash="dash",
                      line_width=1, annotation_text=f"SL ₹{trade['stop_loss']:,.1f}",
                      annotation_position="right", row=1, col=1)
        fig.add_hline(y=trade["target1"],   line_color="#26a641", line_dash="dash",
                      line_width=1, annotation_text=f"T1 ₹{trade['target1']:,.1f}",
                      annotation_position="right", row=1, col=1)
        fig.add_hline(y=trade["target2"],   line_color="#3fb950", line_dash="dot",
                      line_width=1, annotation_text=f"T2 ₹{trade['target2']:,.1f}",
                      annotation_position="right", row=1, col=1)

        # Volume bars
        colors = ["#26a641" if c >= o else "#f85149"
                  for c, o in zip(close, open_)]
        fig.add_trace(go.Bar(
            x=dates, y=volume, name="Volume",
            marker_color=colors, opacity=0.7,
        ), row=2, col=1)

        fig.update_layout(
            height=480,
            template="plotly_dark",
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            margin=dict(l=10, r=80, t=30, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="left", x=0,
                bgcolor="rgba(13,17,23,0.8)",
                bordercolor="#30363d",
                borderwidth=1,
                font=dict(color="#e6edf3", size=12),
            ),
            font=dict(color="#e6edf3"),
            xaxis_rangeslider_visible=False,
            xaxis=dict(gridcolor="#21262d", color="#8b949e"),
            xaxis2=dict(showgrid=False, color="#8b949e"),
            yaxis=dict(gridcolor="#21262d", showgrid=True, color="#8b949e"),
            yaxis2=dict(gridcolor="#21262d", showgrid=True,
                        title=dict(text="Vol", font=dict(color="#8b949e")),
                        color="#8b949e"),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}")
    else:
        st.warning("Chart data not available.")

    # ── TRADINGVIEW DEEP LINK ─────────────────────────────────────────────────
    tv_symbol = "NSE:" + ticker.upper()
    tv_url = f"https://www.tradingview.com/chart/?symbol={tv_symbol}"
    st.markdown(
        f'''<a href="{tv_url}" target="_blank"
            style="display:inline-block;margin-top:8px;padding:8px 20px;
            background:#1c3a5e;color:#58a6ff;border-radius:8px;
            border:1px solid #58a6ff44;text-decoration:none;font-size:0.9rem;">
            📊 Open full interactive chart on TradingView →
        </a>''',
        unsafe_allow_html=True
    )

    st.markdown("")

    # ── AI COMMENTARY (Gemini) ────────────────────────────────────────────────
    st.markdown("**🤖 AI Commentary:**")

    try:
        has_api_key = bool(st.secrets["GEMINI_API_KEY"])
    except (KeyError, FileNotFoundError):
        has_api_key = False

    if has_api_key:
        with st.spinner("Generating AI analysis..."):
            commentary = get_ai_commentary(ticker, trade, score, strategy_key)

        if commentary and not commentary.startswith("__ERROR") and commentary != "__NO_KEY__":
            st.markdown(f"""
            <div style="background:#0d1117;border:1px solid #30363d;
                border-left:4px solid #00d4ff;
                border-radius:8px;padding:16px 18px;margin:8px 0;
                font-size:0.95rem;color:#e6edf3;line-height:1.8;">
                <div style="font-size:10px;font-weight:700;color:#00d4ff;
                    letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">
                    ✦ Gemini AI Analysis
                </div>
                {commentary}
            </div>
            """, unsafe_allow_html=True)
        elif commentary and commentary.startswith("__ERROR"):
            # Show actual error for debugging
            error_msg = commentary.replace("__ERROR_", "").replace("__", "")
            st.error(f"🔴 Gemini API error: {error_msg}")
            st.caption("Share this error message so we can fix it.")
        elif commentary == "__NO_KEY__":
            st.warning("GEMINI_API_KEY found in secrets but returned empty — check for extra spaces in the key.")
        else:
            st.warning("AI commentary returned empty. Try again or check Streamlit logs.")
    else:
        st.markdown("""
        <div style="background:#161b22;border:1px solid #30363d;
            border-left:4px solid #ffd43b;
            border-radius:8px;padding:14px 16px;margin:8px 0;
            font-size:0.9rem;color:#8b949e;">
            <div style="font-size:10px;font-weight:700;color:#ffd43b;
                letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">
                ✦ AI Commentary — Setup Required
            </div>
            <strong style="color:#e6edf3;">Enable free AI commentary in 3 steps:</strong><br><br>
            1. Go to <a href="https://aistudio.google.com" target="_blank"
               style="color:#58a6ff;">aistudio.google.com</a>
               → Sign in with Google → click <strong>Get API Key</strong><br>
            2. Copy your API key (starts with <code>AIza...</code>)<br>
            3. In Streamlit Cloud → your app →
               <strong>Settings → Secrets</strong> → add:<br>
            <code style="display:block;margin-top:8px;padding:8px;
                background:#0d1117;border-radius:4px;color:#58a6ff;">
                GEMINI_API_KEY = "AIza..."
            </code>
            <div style="margin-top:8px;font-size:0.8rem;color:#6e7681;">
                Free tier: 1,500 requests/day · No credit card needed
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.caption("⚠️ Educational only. Not financial advice. Always use your own judgement.")


# ─── MAIN PAGE ────────────────────────────────────────────────────────────────

def render_screener_page():
    st.set_page_config(
        page_title="BullzStock Screener",
        page_icon="🔍",
        layout="wide"
    )
    st.markdown("""
    <style>
    /* ── Global dark fintech theme ── */
    .stApp { background-color: #0d1117; }
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #21262d; }

    /* Sidebar nav */
    section[data-testid="stSidebarNav"] ul li a p {
        text-transform: capitalize !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        color: #8b949e !important;
    }
    section[data-testid="stSidebarNav"] ul li a {
        padding: 6px 12px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #58a6ff !important;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #161b22 !important;
        border: 1px solid #21262d !important;
        border-radius: 10px !important;
        padding: 14px !important;
    }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 11px !important; }
    [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 20px !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid #21262d !important; border-radius: 8px !important; }

    /* Buttons */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #1c3a5e, #185FA5) !important;
        border: 1px solid #58a6ff44 !important;
        border-radius: 8px !important;
        color: #58a6ff !important;
        font-weight: 600 !important;
    }
    [data-testid="baseButton-secondary"] {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #8b949e !important;
    }

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #e6edf3 !important;
    }

    /* Info / warning boxes */
    [data-testid="stInfo"] {
        background: #0d2137 !important;
        border: 1px solid #1c3a5e !important;
        border-radius: 8px !important;
        color: #58a6ff !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: #161b22 !important;
        border: 1px solid #21262d !important;
        border-radius: 8px !important;
    }

    /* Progress bar */
    [data-testid="stProgressBar"] > div > div { background: #58a6ff !important; }

    /* Divider */
    hr { border-color: #21262d !important; }

    /* Text */
    h1,h2,h3,h4 { color: #e6edf3 !important; }
    p, li, span { color: #c9d1d9; }
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:2rem;font-weight:800;
        background:linear-gradient(135deg,#00d4ff,#00ff88);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        margin-bottom:4px;line-height:1.3;">
        🔍 Top 10 Stock Screener — Nifty 50
    </div>
    <div style="color:#8b949e;font-size:0.95rem;margin-bottom:20px;">
        Scans Nifty 50 using RSI · MACD · Volume · Momentum · Trend &nbsp;|&nbsp;
        <span style="color:#58a6ff;">Cached for 1 hour after first scan</span>
    </div>
    """, unsafe_allow_html=True)

    # ── STRATEGY SELECTOR ─────────────────────────────────────────────────────
    st.markdown("#### Select Strategy")
    if "screener_strategy" not in st.session_state:
        st.session_state.screener_strategy = "Momentum"
    # Clear stale strategy keys from old version
    for bad_key in [k for k in list(st.session_state.keys()) if k == "screener_strategy" and st.session_state[k] not in STRATEGIES]:
        del st.session_state[bad_key]

    cols = st.columns(len(STRATEGIES))
    for i, (key, info) in enumerate(STRATEGIES.items()):
        with cols[i]:
            is_selected = st.session_state.screener_strategy == key
            if st.button(
                f"{info['emoji']} {info['label']}\n{info['desc']}",
                key=f"strat_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.screener_strategy = key
                st.rerun()

    selected_strategy = st.session_state.screener_strategy
    info = STRATEGIES[selected_strategy]
    st.info(f"**{info['emoji']} {info['label']}** — {info['desc']}")

    # ── FILTERS ───────────────────────────────────────────────────────────────
    with st.expander("⚙️ Advanced Filters", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            rsi_min, rsi_max = st.slider("RSI Range", 10, 90, (25, 75), key="f_rsi")
        with f2:
            min_vol_surge = st.slider("Min Volume Surge (x avg)", 0.5, 5.0, 1.0, step=0.1, key="f_vol")
        with f3:
            min_momentum = st.slider("Min 20D Return %", -20, 30, -5, key="f_mom")

    # ── BUTTONS ───────────────────────────────────────────────────────────────
    btn_col, _, cache_col = st.columns([2, 4, 2])
    with btn_col:
        run_scan = st.button("🚀 Run Screener", use_container_width=True, type="primary")
    with cache_col:
        if st.button("🔄 Clear Cache & Refresh", use_container_width=True):
            st.cache_data.clear()
            for key in ["raw_data", "screener_df", "screener_strategy_used"]:
                st.session_state.pop(key, None)
            st.toast("Cache cleared!")
            st.rerun()

    # ── FETCH (only on button click) ──────────────────────────────────────────
    if run_scan:
        bar = st.progress(0, text="⏳ Fetching market data for 49 stocks (~2 min first time)...")
        raw_data = fetch_all_stocks(tuple(NIFTY_50))
        bar.progress(60, text="📊 Computing signals...")
        df = compute_signals(raw_data, selected_strategy)
        bar.progress(100, text="✅ Done!")
        time.sleep(0.4)
        bar.empty()
        # Save everything to session state
        st.session_state["raw_data"] = raw_data
        st.session_state["screener_df"] = df
        st.session_state["screener_strategy_used"] = selected_strategy

    # ── RESULTS (read from session state — persists across ALL widget changes) ─
    if "screener_df" not in st.session_state:
        st.info("👆 Select a strategy and click **Run Screener** to scan Nifty 50 stocks.")
        return

    raw_data = st.session_state["raw_data"]
    df       = st.session_state["screener_df"]

    if df.empty:
        st.error("No data returned. Try clicking 'Clear Cache & Refresh' then run again.")
        return

    # ── APPLY FILTERS ─────────────────────────────────────────────────────────
    df_filtered = df[
        (df["_rsi_raw"]       >= rsi_min) &
        (df["_rsi_raw"]       <= rsi_max) &
        (df["_vol_surge_raw"] >= min_vol_surge) &
        (df["_r20_raw"]       >= min_momentum)
    ].copy()

    top10 = df_filtered.head(10)

    # ── METRICS ───────────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Stocks Scanned",   len(raw_data))
    m2.metric("After Filters",    len(df_filtered))
    m3.metric("Top Score",        f"{top10['Score'].iloc[0]:.1f}/100" if not top10.empty else "—")
    m4.metric("Avg RSI (Top 10)", f"{top10['RSI'].mean():.1f}"        if not top10.empty else "—")

    st.markdown("---")
    st.markdown("### 🏆 Top 10 Picks")

    if top10.empty:
        st.warning("No stocks match current filters. Try relaxing the Advanced Filters.")
        return

    # ── TABLE ─────────────────────────────────────────────────────────────────
    display_cols = ["Ticker", "Score", "Price", "RSI", "MACD",
                    "Vol Surge", "5D %", "20D %", "Trend", "Near 52W High"]
    display_df = top10[display_cols].copy()

    def color_score(val):
        if val >= 60:
            return "background-color:#1a472a;color:#40c057;font-weight:700"
        elif val >= 40:
            return "background-color:#2d2a00;color:#ffd43b;font-weight:600"
        else:
            return "background-color:#3b1219;color:#ff6b6b;font-weight:600"

    styled = display_df.style.map(color_score, subset=["Score"])
    st.dataframe(styled, use_container_width=True, height=420)

    # MACD legend
    st.markdown("""
    <div style="display:flex;gap:24px;font-size:0.8rem;color:#8b949e;margin:4px 0 12px 2px;">
        <span>🟢 <strong>Bull Cross</strong> = MACD just crossed above signal (strongest buy)</span>
        <span>🔵 <strong>Bullish</strong> = MACD above signal line (upward momentum)</span>
        <span>🔴 <strong>Bearish</strong> = MACD below signal line (downward pressure)</span>
    </div>
    """, unsafe_allow_html=True)

    # ── STOCK DETAIL PANEL ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 Analyse a Stock — Entry / SL / Targets")

    ticker_options = top10["Ticker"].tolist()
    score_map      = dict(zip(top10["Ticker"], top10["Score"]))

    # Store selected ticker in session state to avoid scroll jump
    if "selected_ticker" not in st.session_state:
        st.session_state["selected_ticker"] = ticker_options[0]

    def on_ticker_change():
        st.session_state["selected_ticker"] = st.session_state["ticker_widget"]

    st.selectbox(
        "Select a stock from the Top 10 list:",
        ticker_options,
        format_func=lambda x: f"{x}  —  Score: {score_map.get(x, 0):.1f}/100",
        key="ticker_widget",
        on_change=on_ticker_change,
        index=ticker_options.index(st.session_state["selected_ticker"])
              if st.session_state["selected_ticker"] in ticker_options else 0
    )

    selected_ticker = st.session_state["selected_ticker"]

    if selected_ticker:
        st.markdown("---")
        render_trade_panel(
            ticker=selected_ticker,
            raw_data=raw_data,
            score=score_map.get(selected_ticker, 50),
            strategy_key=selected_strategy,
        )

    # ── FULL LIST ─────────────────────────────────────────────────────────────
    with st.expander("📋 Full Nifty 50 Rankings"):
        st.dataframe(df_filtered[display_cols] if not df_filtered.empty else df[display_cols],
                     use_container_width=True, height=600)

    # ── DISCLAIMER ────────────────────────────────────────────────────────────
    st.markdown("""
    ---
    > ⚠️ **Disclaimer**: This screener is for educational and research purposes only.
    > It does **not** constitute financial advice. Always do your own research before investing.
    """)


if __name__ == "__main__":
    render_screener_page()

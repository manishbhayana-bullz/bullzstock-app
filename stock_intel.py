bash

cat > /home/claude/screener_v2.py << 'SCREENER_EOF'
#!/usr/bin/env python3
"""
BullzStock Screener — pages/1_Screener.py   v2.0
Rich screener: live price, RSI, trend, volume, candlestick, signal badge,
52W position bar, sector, styled cards. No plain dataframe.
"""

import math
import requests
import streamlit as st
from datetime import datetime

try:
    st.set_page_config(page_title="BullzStock Screener", page_icon="📊", layout="wide")
except Exception:
    pass

# ── Stocks ────────────────────────────────────────────────────
STOCKS = {
    "PFOCUS":     {"name": "PI Focus",        "industry": "IT",          "yf": "PFOCUS.NS",      "tv": "NSE:PFOCUS"},
    "HDFCBANK":   {"name": "HDFC Bank",       "industry": "Banking",     "yf": "HDFCBANK.NS",    "tv": "NSE:HDFCBANK"},
    "ITC":        {"name": "ITC Ltd.",         "industry": "FMCG",        "yf": "ITC.NS",         "tv": "NSE:ITC"},
    "PNB":        {"name": "PNB",             "industry": "Banking",     "yf": "PNB.NS",         "tv": "NSE:PNB"},
    "PAYTM":      {"name": "Paytm",           "industry": "Fintech",     "yf": "PAYTM.NS",       "tv": "NSE:PAYTM"},
    "TATAMOTORS": {"name": "Tata Motors",     "industry": "Automobile",  "yf": "TATAMOTORS.NS",  "tv": "NSE:TATAMOTORS"},
    "HAL":        {"name": "HAL",             "industry": "Defence",     "yf": "HAL.NS",         "tv": "NSE:HAL"},
    "JUBLFOOD":   {"name": "Jubilant Foods",  "industry": "Retail/QSR",  "yf": "JUBLFOOD.NS",    "tv": "NSE:JUBLFOOD"},
}

INDUSTRY_ICONS = {
    "IT": "💻", "Banking": "🏦", "FMCG": "🛒", "Fintech": "💳",
    "Automobile": "🚗", "Defence": "🛡️", "Retail/QSR": "🍕",
}

# ── Maths helpers ─────────────────────────────────────────────
def clean(lst):
    out = []
    for x in (lst or []):
        try:
            v = float(x)
            if not math.isnan(v): out.append(v)
        except: pass
    return out

def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return None
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        if d >= 0: gains += d
        else: losses += abs(d)
    ag, al = gains / period, losses / period
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i-1]
        ag = (ag * (period-1) + (d if d >= 0 else 0)) / period
        al = (al * (period-1) + (abs(d) if d < 0 else 0)) / period
    return 100.0 if al == 0 else 100 - (100 / (1 + ag / al))

def calc_ema(closes, period):
    if len(closes) < period: return None
    k, ema = 2 / (period + 1), closes[0]
    for p in closes[1:]: ema = p * k + ema * (1 - k)
    return ema

def detect_trend(closes):
    if len(closes) < 10: return "N/A"
    mid = len(closes) // 2
    slope = ((closes[-1] - closes[mid]) / closes[mid]) * 100
    if abs(slope) < 1.5:  return "Sideways"
    if slope > 5:         return "↑ Strong Up"
    if slope > 1.5:       return "↑ Mild Up"
    if slope < -5:        return "↓ Strong Down"
    return "↓ Mild Down"

def detect_candle(opens, highs, lows, closes):
    if len(closes) < 3: return "—"
    body = abs(closes[-1] - opens[-1])
    rng  = highs[-1] - lows[-1]
    if rng == 0: return "—"
    uw = highs[-1] - max(closes[-1], opens[-1])
    lw = min(closes[-1], opens[-1]) - lows[-1]
    if lw > body * 2 and uw < body * 0.3: return "Hammer 🔨"
    if uw > body * 2 and lw < body * 0.3: return "Shooting Star ⭐"
    if body < rng * 0.1:                  return "Doji ➖"
    if closes[-1] > closes[-2] and closes[-1] > closes[-3]: return "3 White Sol. ▲"
    if closes[-1] < closes[-2] and closes[-1] < closes[-3]: return "3 Black Crows ▼"
    if closes[-1] > closes[-2] and closes[-1] > opens[-1]:  return "Bull Engulf ▲"
    if closes[-1] < closes[-2] and closes[-1] < opens[-1]:  return "Bear Engulf ▼"
    return "No Pattern"

def quick_signal(closes, ema50, ema200, rsi):
    score = 0
    if rsi:
        if rsi < 30: score += 2
        elif rsi < 45: score += 1
        elif rsi > 70: score -= 2
        elif rsi > 55: score -= 1
    if ema50 and ema200:
        if ema50 > ema200: score += 2
        else: score -= 2
    if len(closes) >= 5:
        slope = (closes[-1] - closes[-5]) / closes[-5] * 100
        if slope > 2: score += 1
        elif slope < -2: score -= 1
    if score >= 3:   return "STRONG BUY",  "#BDFF00", "rgba(189,255,0,0.12)",  "rgba(189,255,0,0.35)"
    if score >= 1:   return "BUY",         "#BDFF00", "rgba(189,255,0,0.08)",  "rgba(189,255,0,0.25)"
    if score <= -3:  return "STRONG SELL", "#ff4d6a", "rgba(255,77,106,0.12)", "rgba(255,77,106,0.35)"
    if score <= -1:  return "SELL",        "#ff4d6a", "rgba(255,77,106,0.08)", "rgba(255,77,106,0.25)"
    return "HOLD/WAIT", "#f5a623", "rgba(245,166,35,0.08)", "rgba(245,166,35,0.25)"

# ── Data fetch — 1-month daily for indicators ─────────────────
@st.cache_data(ttl=180)
def fetch_stock_data(yf_ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_ticker}?range=3mo&interval=1d"
        r   = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if r.status_code != 200: return None
        result = r.json().get("chart", {}).get("result", [None])[0]
        if not result: return None
        meta = result.get("meta", {})
        q    = result.get("indicators", {}).get("quote", [{}])[0]
        opens   = clean(q.get("open",   []))
        highs   = clean(q.get("high",   []))
        lows    = clean(q.get("low",    []))
        closes  = clean(q.get("close",  []))
        volumes = clean(q.get("volume", []))
        if len(closes) < 5: return None
        price = meta.get("regularMarketPrice") or closes[-1]
        prev  = meta.get("previousClose") or closes[-2]
        pct   = (price - prev) / prev * 100 if prev else 0
        vol_recent  = sum(volumes[-3:]) / 3 if len(volumes) >= 3 else 0
        vol_earlier = sum(volumes[-6:-3]) / 3 if len(volumes) >= 6 else vol_recent
        vol_chg = (vol_recent - vol_earlier) / vol_earlier * 100 if vol_earlier else 0
        rsi   = calc_rsi(closes)
        ema50 = calc_ema(closes, min(50, len(closes)))
        ema200= calc_ema(closes, min(200, len(closes)))
        sig, sig_color, sig_bg, sig_border = quick_signal(closes, ema50, ema200, rsi)
        return {
            "price":     price,
            "prev":      prev,
            "pct":       pct,
            "high":      meta.get("regularMarketDayHigh", highs[-1] if highs else price),
            "low":       meta.get("regularMarketDayLow",  lows[-1]  if lows  else price),
            "volume":    meta.get("regularMarketVolume",  volumes[-1] if volumes else 0),
            "w52h":      meta.get("fiftyTwoWeekHigh"),
            "w52l":      meta.get("fiftyTwoWeekLow"),
            "rsi":       rsi,
            "ema50":     ema50,
            "ema200":    ema200,
            "trend":     detect_trend(closes),
            "candle":    detect_candle(opens, highs, lows, closes),
            "vol_chg":   vol_chg,
            "signal":    sig,
            "sig_color": sig_color,
            "sig_bg":    sig_bg,
            "sig_border":sig_border,
            "ema_cross": "Golden Cross ▲" if (ema50 and ema200 and ema50 > ema200) else "Death Cross ▼" if (ema50 and ema200) else "—",
        }
    except Exception:
        return None

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #0a0b0d !important; color: #e3e2e2 !important;
    font-family: 'Manrope', sans-serif !important;
}
[data-testid="stSidebar"] { background: #060709 !important; }
footer { display: none !important; }
.main .block-container { padding-top: 1rem !important; }

.scr-card {
    background: #111315;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.15s;
}
.scr-card:hover { border-color: rgba(189,255,0,0.25); }
.scr-ticker { font-size: 14px; font-weight: 900; color: #e3e2e2; }
.scr-name   { font-size: 10px; color: #6b7a94; margin-left: 6px; }
.scr-price  { font-family: 'IBM Plex Mono', monospace; font-size: 18px; font-weight: 700; }
.scr-pos    { color: #BDFF00; }
.scr-neg    { color: #ff4d6a; }
.scr-neut   { color: #f5a623; }
.scr-pct    { font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600; margin-left: 6px; }
.scr-pill   { display: inline-block; font-size: 9px; font-weight: 700; padding: 2px 7px;
              border-radius: 20px; letter-spacing: 0.04em; margin-right: 4px; }
.scr-row    { display: flex; justify-content: space-between; align-items: center;
              padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
              font-size: 11px; }
.scr-row:last-child { border-bottom: none; }
.scr-key    { color: #6b7a94; }
.scr-val    { font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
.scr-bar-bg { background: rgba(255,255,255,0.06); border-radius: 3px; height: 4px; margin-top: 2px; overflow: hidden; }
.scr-bar-fill { height: 4px; border-radius: 3px; }
.scr-section-title {
    font-size: 9px; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.16em; color: #6b7a94;
    margin: 18px 0 10px; padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.top-card {
    background: #111315; border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 10px 14px; margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
}
.scr-header {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
now = datetime.now().strftime("%H:%M IST · %d %b %Y")
st.markdown(f"""
<div class="scr-header">
  <div style="font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:6px">
    📊 BULLZSTOCK · NSE INDIA · LIVE SCREENER
  </div>
  <div style="font-size:22px;font-weight:900;color:#BDFF00">Market Overview</div>
  <div style="font-size:11px;color:#6b7a94;margin-top:4px">
    3-month daily data · RSI · EMA · Trend · Signal · Refreshes every 3 min · {now}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Industry filter ───────────────────────────────────────────
industries = ["All"] + sorted(set(v["industry"] for v in STOCKS.values()))
col_f1, col_f2 = st.columns([2, 5])
with col_f1:
    chosen_ind = st.selectbox("Filter Industry", industries,
                               format_func=lambda x: f"{INDUSTRY_ICONS.get(x,'📌')} {x}" if x != "All" else "📊 All Industries",
                               label_visibility="collapsed")

filtered = {k: v for k, v in STOCKS.items() if chosen_ind == "All" or v["industry"] == chosen_ind}

# ── Fetch all data ────────────────────────────────────────────
with st.spinner("Fetching live data + computing indicators…"):
    stock_data = {}
    for tkr, info in filtered.items():
        d = fetch_stock_data(info["yf"])
        stock_data[tkr] = d

# ── Top movers ────────────────────────────────────────────────
valid = [(tkr, d) for tkr, d in stock_data.items() if d]
gainers = sorted([x for x in valid if x[1]["pct"] > 0], key=lambda x: x[1]["pct"], reverse=True)
losers  = sorted([x for x in valid if x[1]["pct"] < 0], key=lambda x: x[1]["pct"])

col_g, col_l, col_stats = st.columns([2, 2, 3])

with col_g:
    st.markdown('<div class="scr-section-title">🟢 Top Gainers</div>', unsafe_allow_html=True)
    for tkr, d in gainers[:4]:
        pct_s = f"+{d['pct']:.2f}%"
        st.markdown(f"""
        <div class="top-card">
          <div>
            <span style="font-size:12px;font-weight:800;color:#e3e2e2">{tkr}</span>
            <span style="font-size:9px;color:#6b7a94;margin-left:5px">{STOCKS[tkr]['name']}</span>
          </div>
          <div style="text-align:right">
            <span style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#e3e2e2">₹{d['price']:,.2f}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#BDFF00;margin-left:5px">{pct_s}</span>
          </div>
        </div>""", unsafe_allow_html=True)

with col_l:
    st.markdown('<div class="scr-section-title">🔴 Top Losers</div>', unsafe_allow_html=True)
    for tkr, d in losers[:4]:
        pct_s = f"{d['pct']:.2f}%"
        st.markdown(f"""
        <div class="top-card">
          <div>
            <span style="font-size:12px;font-weight:800;color:#e3e2e2">{tkr}</span>
            <span style="font-size:9px;color:#6b7a94;margin-left:5px">{STOCKS[tkr]['name']}</span>
          </div>
          <div style="text-align:right">
            <span style="font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#e3e2e2">₹{d['price']:,.2f}</span>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#ff4d6a;margin-left:5px">{pct_s}</span>
          </div>
        </div>""", unsafe_allow_html=True)

with col_stats:
    st.markdown('<div class="scr-section-title">📈 Market Pulse</div>', unsafe_allow_html=True)
    if valid:
        all_pcts = [d["pct"] for _, d in valid]
        bull_count = sum(1 for p in all_pcts if p > 0)
        bear_count = sum(1 for p in all_pcts if p < 0)
        buy_sig   = sum(1 for _, d in valid if "BUY" in d["signal"])
        sell_sig  = sum(1 for _, d in valid if "SELL" in d["signal"])
        avg_rsi   = sum(d["rsi"] for _, d in valid if d.get("rsi")) / max(len([d for _, d in valid if d.get("rsi")]), 1)
        total = len(valid)
        bull_pct = bull_count / total * 100
        bull_w = f"{bull_pct:.0f}%"
        bear_w = f"{(100-bull_pct):.0f}%"
        st.markdown(f"""
        <div style="background:#111315;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:12px 14px">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
            <div style="text-align:center;background:rgba(189,255,0,0.06);border:1px solid rgba(189,255,0,0.2);border-radius:8px;padding:8px">
              <div style="font-size:20px;font-weight:900;color:#BDFF00">{bull_count}</div>
              <div style="font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.1em">Advancing</div>
            </div>
            <div style="text-align:center;background:rgba(255,77,106,0.06);border:1px solid rgba(255,77,106,0.2);border-radius:8px;padding:8px">
              <div style="font-size:20px;font-weight:900;color:#ff4d6a">{bear_count}</div>
              <div style="font-size:9px;color:#6b7a94;text-transform:uppercase;letter-spacing:0.1em">Declining</div>
            </div>
          </div>
          <div style="font-size:9px;color:#6b7a94;margin-bottom:4px">Bull/Bear Split</div>
          <div style="display:flex;height:5px;border-radius:3px;overflow:hidden;margin-bottom:10px">
            <div style="width:{bull_w};background:#BDFF00"></div>
            <div style="width:{bear_w};background:#ff4d6a"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:10px;color:#6b7a94">
            <span>Buy signals: <b style="color:#BDFF00">{buy_sig}</b></span>
            <span>Sell signals: <b style="color:#ff4d6a">{sell_sig}</b></span>
            <span>Avg RSI: <b style="color:#f5a623">{avg_rsi:.1f}</b></span>
          </div>
        </div>""", unsafe_allow_html=True)

# ── Stock cards grid ──────────────────────────────────────────
st.markdown('<div class="scr-section-title">📋 All Stocks — Full Detail</div>', unsafe_allow_html=True)

cols_per_row = 2
tkr_list = list(filtered.keys())
for i in range(0, len(tkr_list), cols_per_row):
    row_cols = st.columns(cols_per_row)
    for j, col in enumerate(row_cols):
        if i + j >= len(tkr_list): break
        tkr  = tkr_list[i + j]
        info = STOCKS[tkr]
        d    = stock_data.get(tkr)
        with col:
            if not d:
                st.markdown(f"""<div class="scr-card">
                  <span class="scr-ticker">{tkr}</span>
                  <span class="scr-name">{info['name']}</span>
                  <div style="color:#6b7a94;font-size:11px;margin-top:8px">⚠️ Data unavailable (market may be closed)</div>
                </div>""", unsafe_allow_html=True)
                continue

            pct_cls   = "scr-pos" if d["pct"] >= 0 else "scr-neg"
            pct_str   = f"{'+' if d['pct'] >= 0 else ''}{d['pct']:.2f}%"
            chg_sym   = "▲" if d["pct"] >= 0 else "▼"
            rsi_val   = d.get("rsi")
            rsi_str   = f"{rsi_val:.1f}" if rsi_val else "—"
            rsi_cls   = "scr-neg" if (rsi_val or 50) > 70 else "scr-pos" if (rsi_val or 50) < 30 else "scr-neut"
            rsi_lbl   = "Overbought" if (rsi_val or 50) > 70 else "Oversold" if (rsi_val or 50) < 30 else "Neutral"
            vol_str   = f"{d['volume']/1e5:.1f}L" if d.get("volume") else "—"
            vol_chg   = d.get("vol_chg", 0)
            vol_c     = "#BDFF00" if vol_chg > 15 else "#ff4d6a" if vol_chg < -15 else "#8b949e"
            vol_chg_s = f"{'+' if vol_chg >= 0 else ''}{vol_chg:.0f}%"

            # 52W position bar
            w52h, w52l = d.get("w52h"), d.get("w52l")
            bar_html = ""
            if w52h and w52l and w52h > w52l:
                pos_pct = min(max((d["price"] - w52l) / (w52h - w52l) * 100, 0), 100)
                bar_c   = "#BDFF00" if pos_pct > 70 else "#f5a623" if pos_pct > 40 else "#ff4d6a"
                bar_html = f"""
                <div style="margin-top:8px">
                  <div style="display:flex;justify-content:space-between;font-size:9px;color:#6b7a94;margin-bottom:2px">
                    <span>52W Low ₹{w52l:,.0f}</span>
                    <span style="color:{bar_c}">{pos_pct:.0f}% of range</span>
                    <span>52W High ₹{w52h:,.0f}</span>
                  </div>
                  <div class="scr-bar-bg">
                    <div class="scr-bar-fill" style="width:{pos_pct:.0f}%;background:{bar_c}"></div>
                  </div>
                </div>"""

            # EMA cross badge
            cross   = d.get("ema_cross", "—")
            cross_c = "#BDFF00" if "Golden" in cross else "#ff4d6a" if "Death" in cross else "#8b949e"
            cross_bg= "rgba(189,255,0,0.08)" if "Golden" in cross else "rgba(255,77,106,0.08)" if "Death" in cross else "rgba(255,255,255,0.05)"

            # Signal badge
            sig_c  = d["sig_color"]
            sig_bg_ = d["sig_bg"]
            sig_bd  = d["sig_border"]

            ind_icon = INDUSTRY_ICONS.get(info["industry"], "📌")

            st.markdown(f"""
            <div class="scr-card">
              <!-- Header row -->
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
                <div>
                  <span class="scr-ticker">{tkr}</span>
                  <span class="scr-name">{ind_icon} {info['name']} · {info['industry']}</span>
                  <div style="margin-top:4px">
                    <span class="scr-pill" style="background:{sig_bg_};color:{sig_c};border:1px solid {sig_bd}">{d['signal']}</span>
                    <span class="scr-pill" style="background:{cross_bg};color:{cross_c};border:1px solid {cross_c}22">{cross}</span>
                  </div>
                </div>
                <div style="text-align:right">
                  <div class="scr-price {pct_cls}">₹{d['price']:,.2f}</div>
                  <div class="scr-pct {pct_cls}">{chg_sym} {pct_str}</div>
                </div>
              </div>

              <!-- Indicator rows -->
              <div class="scr-row">
                <span class="scr-key">RSI (14)</span>
                <span class="scr-val {rsi_cls}">{rsi_str} <span style="font-size:9px;color:#6b7a94">({rsi_lbl})</span></span>
              </div>
              <div class="scr-row">
                <span class="scr-key">EMA 50 / 200</span>
                <span class="scr-val">₹{d['ema50']:,.1f} / ₹{d['ema200']:,.1f}</span>
              </div>
              <div class="scr-row">
                <span class="scr-key">Trend</span>
                <span class="scr-val" style="color:{'#BDFF00' if 'Up' in d['trend'] else '#ff4d6a' if 'Down' in d['trend'] else '#f5a623'}">{d['trend']}</span>
              </div>
              <div class="scr-row">
                <span class="scr-key">Candlestick</span>
                <span class="scr-val" style="color:#8b949e">{d['candle']}</span>
              </div>
              <div class="scr-row">
                <span class="scr-key">Volume</span>
                <span class="scr-val">{vol_str} <span style="color:{vol_c};font-size:10px">({vol_chg_s} vs avg)</span></span>
              </div>
              <div class="scr-row">
                <span class="scr-key">Day H / L</span>
                <span class="scr-val">₹{d['high']:,.2f} / ₹{d['low']:,.2f}</span>
              </div>
              {bar_html}
            </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────
st.markdown("""
<div style="font-size:10px;color:#6b7a94;padding:10px 14px;background:rgba(255,255,255,0.02);
     border:1px solid rgba(255,255,255,0.05);border-radius:8px;line-height:1.6;margin-top:14px">
  ⚠️ Data from Yahoo Finance. Signals are rule-based indicator confluence —
  <b>not financial advice</b>. Always consult a SEBI-registered investment advisor.
  NSE hours: Mon–Fri 9:15 AM – 3:30 PM IST.
</div>""", unsafe_allow_html=True)
SCREENER_EOF

python3 -c "import ast; ast.parse(open('/home/claude/screener_v2.py').read()); print('✅ Screener v2 syntax OK')"
Output

✅ Screener v2 syntax OK

#!/usr/bin/env python3
"""
BullzStock Screener — pages/1_Screener.py
Drop this into a `pages/` subfolder next to stock_intel_v4_2.py.
It has its own page config so it never conflicts with main app.
"""

import requests
import math
import streamlit as st

# ── Page config — MUST be first Streamlit call ───────────────
try:
    st.set_page_config(
        page_title="BullzStock Screener",
        page_icon="📊",
        layout="wide",
    )
except Exception:
    pass  # already set when run from pages/ context

STOCKS = {
    "PFOCUS":     {"name": "PI Focus",       "industry": "IT",         "yf": "PFOCUS.NS"},
    "HDFCBANK":   {"name": "HDFC Bank",      "industry": "Banking",    "yf": "HDFCBANK.NS"},
    "ITC":        {"name": "ITC Ltd.",        "industry": "FMCG",       "yf": "ITC.NS"},
    "PNB":        {"name": "PNB",            "industry": "Banking",    "yf": "PNB.NS"},
    "PAYTM":      {"name": "Paytm",          "industry": "Fintech",    "yf": "PAYTM.NS"},
    "TATAMOTORS": {"name": "Tata Motors",    "industry": "Automobile", "yf": "TATAMOTORS.NS"},
    "HAL":        {"name": "HAL",            "industry": "Defence",    "yf": "HAL.NS"},
    "JUBLFOOD":   {"name": "Jubilant Foods", "industry": "Retail/QSR", "yf": "JUBLFOOD.NS"},
}

@st.cache_data(ttl=120)
def fetch_quick_price(yf_ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_ticker}?range=1d&interval=1d"
        r   = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if r.status_code == 200:
            meta  = r.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice") or meta.get("chartPreviousClose")
            prev  = meta.get("previousClose") or meta.get("chartPreviousClose")
            w52h  = meta.get("fiftyTwoWeekHigh")
            w52l  = meta.get("fiftyTwoWeekLow")
            if price and prev and prev > 0:
                pct = (price - prev) / prev * 100
                return {"price": price, "pct": pct, "52wH": w52h, "52wL": w52l}
    except Exception:
        pass
    return None

st.markdown("## 📊 BullzStock Screener")
st.caption("Live NSE prices · Refreshes every 2 minutes · Click Analyse on main page for signals")

with st.spinner("Fetching live prices…"):
    rows = []
    for tkr, info in STOCKS.items():
        qp = fetch_quick_price(info["yf"])
        if qp:
            pct_val = qp["pct"]
            rows.append({
                "Ticker":    tkr,
                "Name":      info["name"],
                "Industry":  info["industry"],
                "Price (₹)": f"₹{qp['price']:,.2f}",
                "Change %":  f"{'+' if pct_val >= 0 else ''}{pct_val:.2f}%",
                "52W High":  f"₹{qp['52wH']:,.2f}" if qp.get("52wH") else "—",
                "52W Low":   f"₹{qp['52wL']:,.2f}" if qp.get("52wL") else "—",
                "_pct":      pct_val,
            })
        else:
            rows.append({
                "Ticker": tkr, "Name": info["name"], "Industry": info["industry"],
                "Price (₹)": "—", "Change %": "—", "52W High": "—", "52W Low": "—",
                "_pct": 0,
            })

if rows:
    gainers = sorted([r for r in rows if r["_pct"] > 0], key=lambda x: x["_pct"], reverse=True)
    losers  = sorted([r for r in rows if r["_pct"] < 0], key=lambda x: x["_pct"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🟢 Top Gainers")
        for r in gainers[:4]:
            st.markdown(f"**{r['Ticker']}** — {r['Price (₹)']} `{r['Change %']}`")
    with c2:
        st.markdown("### 🔴 Top Losers")
        for r in losers[:4]:
            st.markdown(f"**{r['Ticker']}** — {r['Price (₹)']} `{r['Change %']}`")

    st.markdown("---")
    display_rows = [{k: v for k, v in r.items() if k != "_pct"} for r in rows]
    st.dataframe(display_rows, use_container_width=True)
else:
    st.warning("No data available. Markets may be closed or Yahoo Finance is rate-limiting.")

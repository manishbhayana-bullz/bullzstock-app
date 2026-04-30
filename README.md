# MB Stock Intelligence 📊

**A free AI-powered stock analysis tool for NSE India — built by a Delivery Manager, not a developer.**

🔗 **Live App:** [bullzstock-app.streamlit.app](https://bullzstock-app.streamlit.app)

---

## What this is

MB Stock Intelligence scans all Nifty 50 stocks using technical indicators and generates actionable trade setups — with AI commentary explaining every signal in plain English.

Built using Python, Streamlit, and Claude AI. No dev team. No infrastructure cost. Fully deployed and live.

---

## What it does

| Feature | Detail |
|---|---|
| 📈 Technical Scan | RSI, MACD, Volume & Momentum across all Nifty 50 stocks |
| 🎯 Trade Setups | Entry price, Stop Loss, Target 1 & Target 2 with Risk:Reward ratio |
| 🤖 AI Commentary | Claude API explains each signal in plain English |
| 📊 Charts | Plotly candlestick charts with trade levels drawn directly on the chart |
| 📲 Telegram Alerts | Buy/sell signal notifications via Telegram bot |
| 🔁 Data Fallback | Alpha Vantage as automatic backup when Yahoo Finance fails |

---

## Why I built this

10 crore+ Indians now have demat accounts. Most of them overtrade based on tips from YouTube and Twitter. Zerodha and Groww show charts. Screener.in covers fundamentals. Nobody was giving free, actionable technical signals with complete trade setups.

That was the gap. This is the bridge.

---

## Tech stack

- **Frontend & Deployment:** Streamlit (free tier, Streamlit Cloud)
- **Data — Primary:** Yahoo Finance (`yfinance`)
- **Data — Backup:** Alpha Vantage API
- **Indicators:** `pandas-ta` (RSI, MACD, Volume, Momentum)
- **Charts:** Plotly (candlestick with trade levels)
- **AI Layer:** Anthropic Claude API
- **Notifications:** Telegram Bot API
- **Language:** Python 3.x

---

## Architecture decisions & why

### Why Alpha Vantage as fallback?
Yahoo Finance is free and fast but unreliable for NSE symbols — it fails silently, returning empty dataframes with no error. Rather than show users a broken screen, I added Alpha Vantage as an automatic fallback. If Yahoo Finance returns empty data, Alpha Vantage kicks in transparently. Users never see the failure.

**Lesson:** In data-heavy apps, silent failures are more dangerous than loud ones. Design for them explicitly.

### Why Plotly instead of TradingView?
Initially used TradingView charts via iframe embed. After deployment, every NSE stock was rendering Apple (AAPL) charts instead — because Streamlit caches iframe components by content hash, and the browser was serving stale cached content regardless of the stock selected.

Removing the iframe entirely and switching to Plotly reading directly from in-memory fetched data fixed the issue permanently. No network call, no caching, always the correct stock.

**Lesson:** The best fix is often removing a dependency entirely, not patching around it.

### Why redesign Streamlit session state?
Every dropdown change was triggering a full page reset, wiping user selections and re-running all API calls from scratch. This made the app unusable for multi-stock comparison.

Redesigned the flow using `st.session_state` to persist user selections and cache fetched data separately from UI state. Dropdowns now update the view without resetting the entire session.

**Lesson:** Streamlit's execution model re-runs the entire script on every interaction. If you don't explicitly manage state, you're building a stateless app by accident.

### Why normalise Pandas output before indicator calculation?
A `pandas-ta` update changed how it returned indicator data — Series format changed silently, with no deprecation warning. All RSI and MACD calculations started returning NaN without any error message.

Added a normalisation step before every indicator calculation that enforces expected data types and shape. Now library updates don't silently break signal logic.

**Lesson:** Third-party library updates break things quietly. Validate your data shape at every pipeline boundary.

---

## Known limitations & honest tradeoffs

This section exists because I think transparency about tradeoffs is more useful than pretending everything is perfect.

**UI & Styling**
Streamlit's free tier has real constraints around fonts, layout control, and component-level styling. Some visual rough edges exist because of these platform limits, not design choices.

**Where I made a conscious call to ship over polish**
A few UI fixes were causing regressions elsewhere — fixing font rendering was breaking chart alignment, fixing spacing was affecting mobile layout. At some point you decide to ship a working product and iterate on polish later. That's the call I made. The logic, signals, and AI commentary all work correctly. The UI will improve in future iterations.

**Rate limits**
Alpha Vantage free tier has API rate limits (5 calls/minute, 500/day). For heavy usage or real-time scanning, a paid plan would be needed.

**Not financial advice**
This tool generates technical signals based on indicator logic. It is not financial advice. Always apply your own judgement before any trade.

---

## What I learned building this

I've spent 10+ years in delivery management, BA, QA, and scrum. I thought I understood what "building a product" meant. Building this alone taught me things I couldn't have learned from any PRD:

- Silent failures are the hardest bugs to catch — and the most common in real data pipelines
- Dependency management is a product risk, not just a technical one
- Shipping something imperfect and learning from real users beats waiting for perfect
- Understanding how something breaks is more valuable than knowing how it works

---

## Project status

✅ Live and deployed
🔄 Active iteration — UI improvements, additional indicators, and sector-level scanning in backlog

---

## Author

**Manish Bhayana**
Senior Delivery Manager | AI Product Builder
[LinkedIn](https://linkedin.com/in/your-profile) | manishbhayana@gmail.com

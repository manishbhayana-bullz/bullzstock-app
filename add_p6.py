"""
Run from bullz_clean folder:
    python3 add_p6.py

Adds Claude AI commentary to the trade panel.
Generates natural language stock analysis using Claude API.
"""

SCREENER_PATH = "/Users/manishbhayana/bullz_clean/pages/2_Screener.py"

with open(SCREENER_PATH, "r") as f:
    content = f.read()

# ─── NEW: Claude AI Commentary Function ───────────────────────────────────────
CLAUDE_FUNCTION = '''
# ─── P6: CLAUDE AI COMMENTARY ─────────────────────────────────────────────────

def get_claude_commentary(ticker, trade, score, strategy_key):
    """
    Call Claude API to generate natural language stock commentary.
    Uses the trade signal data already computed — no extra data fetch needed.
    """
    import requests
    import json
    import streamlit as st

    # Build a rich prompt from computed signal data
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

Write a 3-4 line commentary that:
1. Summarizes the current technical picture in plain English
2. Explains the key reason for the signal (bullish/bearish/neutral)
3. Mentions the key risk to watch
4. Ends with one actionable sentence

Be direct and specific. Use Indian market context. No disclaimers needed."""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": st.secrets.get("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"].strip()
        else:
            return None
    except Exception:
        return None

'''

# Insert before render_trade_panel
if "get_claude_commentary" not in content:
    content = content.replace(
        "def render_trade_panel(ticker, raw_data, score, strategy_key):",
        CLAUDE_FUNCTION + "\ndef render_trade_panel(ticker, raw_data, score, strategy_key):"
    )
    print("✅ Claude commentary function added")
else:
    print("⚠️  Claude function already exists")

# ─── ADD AI COMMENTARY BLOCK inside render_trade_panel ────────────────────────
OLD_CAPTION = '''    st.markdown("")
    st.caption("⚠️ Educational only. Not financial advice. Always use your own judgement.")'''

NEW_CAPTION = '''    st.markdown("")

    # ── P6: AI COMMENTARY ─────────────────────────────────────────────────────
    st.markdown("**🤖 AI Commentary:**")

    import streamlit as st_inner
    has_api_key = bool(st_inner.secrets.get("ANTHROPIC_API_KEY", ""))

    if has_api_key:
        with st.spinner("Generating AI analysis..."):
            commentary = get_claude_commentary(ticker, trade, score, strategy_key)
        if commentary:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-left:3px solid #58a6ff;
                border-radius:8px;padding:14px 16px;margin:8px 0;
                font-size:0.95rem;color:#e6edf3;line-height:1.7;">
                {commentary}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("AI commentary unavailable right now.")
    else:
        st.markdown("""
        <div style="background:#161b22;border:1px solid #30363d;border-left:3px solid #ffd43b;
            border-radius:8px;padding:12px 16px;margin:8px 0;font-size:0.9rem;color:#8b949e;">
            🔑 Add your Anthropic API key in Streamlit Cloud Secrets to enable AI commentary.<br>
            <code>ANTHROPIC_API_KEY = "sk-ant-..."</code>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.caption("⚠️ Educational only. Not financial advice. Always use your own judgement.")'''

if OLD_CAPTION in content:
    content = content.replace(OLD_CAPTION, NEW_CAPTION)
    print("✅ AI commentary block added to trade panel")
else:
    print("❌ Caption block not found exactly")

# ─── SAVE ─────────────────────────────────────────────────────────────────────
with open(SCREENER_PATH, "w") as f:
    f.write(content)

print("\n✅ P6 done. Next steps:")
print("1. Add ANTHROPIC_API_KEY to Streamlit Cloud Secrets")
print("2. Run: pkill -f streamlit; sleep 2; streamlit run stock_intel.py")
print("3. Test locally first — needs ANTHROPIC_API_KEY in .streamlit/secrets.toml")

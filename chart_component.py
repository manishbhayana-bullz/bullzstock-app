"""
P4 - TradingView Chart Component for Streamlit
Replaces Plotly charts with embedded TradingView widgets
Gives exact Groww/Zerodha look with zero extra cost
"""

import streamlit as st
import streamlit.components.v1 as components


# Map common Indian stock names to TradingView symbols
NSE_SYMBOL_MAP = {
    "RELIANCE": "NSE:RELIANCE",
    "TCS": "NSE:TCS",
    "INFY": "NSE:INFY",
    "HDFCBANK": "NSE:HDFCBANK",
    "ICICIBANK": "NSE:ICICIBANK",
    "HINDUNILVR": "NSE:HINDUNILVR",
    "ITC": "NSE:ITC",
    "SBIN": "NSE:SBIN",
    "BAJFINANCE": "NSE:BAJFINANCE",
    "BHARTIARTL": "NSE:BHARTIARTL",
    "WIPRO": "NSE:WIPRO",
    "HCLTECH": "NSE:HCLTECH",
    "AXISBANK": "NSE:AXISBANK",
    "KOTAKBANK": "NSE:KOTAKBANK",
    "LT": "NSE:LT",
    "ASIANPAINT": "NSE:ASIANPAINT",
    "MARUTI": "NSE:MARUTI",
    "TITAN": "NSE:TITAN",
    "SUNPHARMA": "NSE:SUNPHARMA",
    "ULTRACEMCO": "NSE:ULTRACEMCO",
    "NESTLEIND": "NSE:NESTLEIND",
    "POWERGRID": "NSE:POWERGRID",
    "NTPC": "NSE:NTPC",
    "ONGC": "NSE:ONGC",
    "TATAMOTORS": "NSE:TATAMOTORS",
    "TATASTEEL": "NSE:TATASTEEL",
    "ADANIPORTS": "NSE:ADANIPORTS",
    "JSWSTEEL": "NSE:JSWSTEEL",
    "TECHM": "NSE:TECHM",
    "DRREDDY": "NSE:DRREDDY",
    # Add more as needed
}

INTERVAL_MAP = {
    "1 min": "1",
    "5 min": "5",
    "15 min": "15",
    "30 min": "30",
    "1 Hour": "60",
    "1 Day": "D",
    "1 Week": "W",
    "1 Month": "M",
}

STUDY_MAP = {
    "RSI": "RSI@tv-basicstudies",
    "MACD": "MACD@tv-basicstudies",
    "Bollinger Bands": "BB@tv-basicstudies",
    "Volume": "Volume@tv-basicstudies",
    "EMA 20": "MAExp@tv-basicstudies",
    "SMA 50": "MASimple@tv-basicstudies",
    "Stochastic": "Stochastic@tv-basicstudies",
    "ATR": "ATR@tv-basicstudies",
}


def get_tv_symbol(ticker: str) -> str:
    """Convert ticker to TradingView NSE format"""
    ticker = ticker.upper().replace(".NS", "").replace(".BO", "")
    return NSE_SYMBOL_MAP.get(ticker, f"NSE:{ticker}")


def render_tradingview_chart(
    ticker: str,
    interval: str = "D",
    height: int = 520,
    theme: str = "dark",
    studies: list = None,
    show_toolbar: bool = True,
    container_key: str = "tv_chart",
):
    """
    Render a full TradingView Advanced Chart widget in Streamlit.
    
    Args:
        ticker: Stock symbol (e.g. 'RELIANCE', 'TCS')
        interval: Chart interval ('1','5','15','30','60','D','W','M')
        height: Widget height in pixels
        theme: 'dark' or 'light'
        studies: List of indicator keys from STUDY_MAP
        show_toolbar: Show the top drawing toolbar
        container_key: Unique key for Streamlit component
    """
    if studies is None:
        studies = ["Volume", "RSI"]

    tv_symbol = get_tv_symbol(ticker)

    # Build studies JSON array
    studies_json = []
    for s in studies:
        tv_study = STUDY_MAP.get(s)
        if tv_study:
            studies_json.append(f'"{tv_study}"')
    studies_str = "[" + ", ".join(studies_json) + "]"

    bg_color = "#0d1117" if theme == "dark" else "#ffffff"
    toolbar_bg = "#161b22" if theme == "dark" else "#f8f9fa"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{
                width: 100%;
                height: 100%;
                background: {bg_color};
                overflow: hidden;
            }}
            .tv-wrapper {{
                width: 100%;
                height: {height}px;
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid {"#30363d" if theme == "dark" else "#e1e4e8"};
            }}
            .tradingview-widget-container {{
                height: 100%;
                width: 100%;
            }}
            .tradingview-widget-container__widget {{
                height: calc(100% - 32px);
                width: 100%;
            }}
            .tradingview-widget-copyright {{
                font-size: 11px;
                line-height: 32px;
                text-align: center;
                color: {"#6e7681" if theme == "dark" else "#888"};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: {toolbar_bg};
            }}
            .tradingview-widget-copyright a {{
                color: {"#58a6ff" if theme == "dark" else "#0366d6"};
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="tv-wrapper">
            <div class="tradingview-widget-container">
                <div class="tradingview-widget-container__widget"></div>
                <div class="tradingview-widget-copyright">
                    <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
                        Track all markets on TradingView
                    </a>
                </div>
                <script type="text/javascript" 
                    src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" 
                    async>
                {{
                    "autosize": true,
                    "symbol": "{tv_symbol}",
                    "interval": "{interval}",
                    "timezone": "Asia/Kolkata",
                    "theme": "{theme}",
                    "style": "1",
                    "locale": "en",
                    "backgroundColor": "{bg_color}",
                    "gridColor": "{"rgba(255,255,255,0.04)" if theme == "dark" else "rgba(0,0,0,0.04)"}",
                    "hide_top_toolbar": {str(not show_toolbar).lower()},
                    "hide_legend": false,
                    "allow_symbol_change": true,
                    "save_image": true,
                    "calendar": false,
                    "studies": {studies_str},
                    "support_host": "https://www.tradingview.com"
                }}
                </script>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html_code, height=height + 40, scrolling=False)


def render_symbol_overview(
    tickers: list,
    theme: str = "dark",
    height: int = 160,
):
    """
    Render a TradingView Symbol Overview mini-widget (price + sparkline).
    Great for showing multiple stocks at a glance.
    
    Args:
        tickers: List of ticker strings
        theme: 'dark' or 'light'
        height: Widget height
    """
    symbols = []
    for t in tickers:
        tv_sym = get_tv_symbol(t)
        symbols.append(f'["{tv_sym}", "{t}"]')
    symbols_str = "[" + ", ".join(symbols) + "]"

    bg_color = "#0d1117" if theme == "dark" else "#ffffff"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: {bg_color}; overflow: hidden; }}
            .tradingview-widget-container {{ width: 100%; height: {height}px; }}
        </style>
    </head>
    <body>
        <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js"
                async>
            {{
                "symbols": {symbols_str},
                "chartOnly": false,
                "width": "100%",
                "height": "{height}",
                "locale": "en",
                "colorTheme": "{theme}",
                "autosize": true,
                "showVolume": false,
                "showMA": false,
                "hideDateRanges": false,
                "hideMarketStatus": false,
                "hideSymbolLogo": false,
                "scalePosition": "right",
                "scaleMode": "Normal",
                "fontFamily": "-apple-system, BlinkMacSystemFont, Trebuchet MS, Roboto, Ubuntu, sans-serif",
                "fontSize": "10",
                "noTimeScale": false,
                "valuesTracking": "1",
                "changeMode": "price-and-percent",
                "chartType": "area",
                "maLineColor": "#2962FF",
                "maLineWidth": 1,
                "maLength": 9,
                "backgroundColor": "{bg_color}",
                "lineWidth": 2,
                "lineType": 0,
                "dateRanges": ["1d|1", "1m|30", "3m|60", "12m|1D", "60m|1W", "all|1M"]
            }}
            </script>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=height + 20, scrolling=False)


def render_market_overview(theme: str = "dark", height: int = 400):
    """
    Render TradingView Market Overview widget.
    Shows Nifty 50, Sensex, sector performance etc.
    """
    bg_color = "#0d1117" if theme == "dark" else "#ffffff"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background: {bg_color}; overflow: hidden; }}
            .tradingview-widget-container {{ width: 100%; height: {height}px; }}
        </style>
    </head>
    <body>
        <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js"
                async>
            {{
                "colorTheme": "{theme}",
                "dateRange": "12M",
                "showChart": true,
                "locale": "en",
                "largeChartUrl": "",
                "isTransparent": false,
                "showSymbolLogo": true,
                "showFloatingTooltip": false,
                "width": "100%",
                "height": "{height}",
                "tabs": [
                    {{
                        "title": "Indices",
                        "symbols": [
                            {{"s": "BSE:SENSEX", "d": "Sensex"}},
                            {{"s": "NSE:NIFTY", "d": "Nifty 50"}},
                            {{"s": "NSE:BANKNIFTY", "d": "Bank Nifty"}},
                            {{"s": "NSE:NIFTYMIDCAP100", "d": "Midcap 100"}},
                            {{"s": "NSE:CNXIT", "d": "Nifty IT"}}
                        ],
                        "originalTitle": "Indices"
                    }},
                    {{
                        "title": "Top Stocks",
                        "symbols": [
                            {{"s": "NSE:RELIANCE", "d": "Reliance"}},
                            {{"s": "NSE:TCS", "d": "TCS"}},
                            {{"s": "NSE:HDFCBANK", "d": "HDFC Bank"}},
                            {{"s": "NSE:INFY", "d": "Infosys"}},
                            {{"s": "NSE:ICICIBANK", "d": "ICICI Bank"}},
                            {{"s": "NSE:SBIN", "d": "SBI"}}
                        ],
                        "originalTitle": "Stocks"
                    }}
                ]
            }}
            </script>
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=height + 20, scrolling=False)


# ─── USAGE EXAMPLE (for your main app) ────────────────────────────────────────
def chart_section_example():
    """
    Drop-in replacement for your existing Plotly chart section.
    Copy this pattern into your main app.
    """
    st.markdown("### 📈 Price Chart")

    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        interval_label = st.selectbox(
            "Interval",
            list(INTERVAL_MAP.keys()),
            index=5,  # Default: 1 Day
            key="chart_interval"
        )

    with col2:
        chart_theme = st.selectbox(
            "Theme",
            ["dark", "light"],
            index=0,
            key="chart_theme"
        )

    with col3:
        selected_studies = st.multiselect(
            "Indicators",
            list(STUDY_MAP.keys()),
            default=["Volume", "RSI"],
            key="chart_studies"
        )

    interval = INTERVAL_MAP[interval_label]

    # This single call replaces ALL your Plotly chart code
    render_tradingview_chart(
        ticker=st.session_state.get("selected_ticker", "RELIANCE"),
        interval=interval,
        height=520,
        theme=chart_theme,
        studies=selected_studies,
    )

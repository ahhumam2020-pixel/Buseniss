import yfinance as yf
import datetime, pytz
import pandas as pd
import numpy as np
import os

# --- تنظیمات سیستمی ---
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = "index.html"
APP_TITLE = "Global Quantamental Insight Hub V4.0"

# --- لیست دارایی‌های استراتژیک ---
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'NSDQ100': {'ticker': 'NQ=F', 'tv_symbol': 'CAPITALCOM:US100'},
    'SP500': {'ticker': 'ES=F', 'tv_symbol': 'CAPITALCOM:US500'},
    'CHINA50': {'ticker': 'XIN9.FGI', 'tv_symbol': 'FX_IDC:CHINAA50'},
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'}
}

def get_fundamental_bias(ticker, dxy_change):
    """تحلیل بنیادی بر اساس همبستگی معکوس با شاخص دلار (DXY)"""
    is_inverse = any(x in ticker for x in ['GC=F', 'NQ=F', 'ES=F', 'XIN9'])
    if is_inverse:
        return "BULLISH" if dxy_change < 0 else "BEARISH"
    return "BULLISH" if dxy_change > 0 else "BEARISH"

def generate_dashboard():
    print(f"--- Starting {APP_TITLE} ---")
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    
    # ۱. دریافت داده بنیادی (شاخص دلار)
    print("Step 1: Analyzing DXY for Fundamental Filter...")
    try:
        dxy = yf.download("DX-Y.NYB", period="2d", interval="1d", progress=False)
        dxy_change = ((dxy['Close'].iloc[-1] - dxy['Close'].iloc[-2]) / dxy['Close'].iloc[-2]) * 100
        print(f"DXY Change: {dxy_change:+.2f}%")
    except Exception as e:
        print(f"DXY Error: {e}")
        dxy_change = 0

    cards_html = ""
    
    # ۲. پردازش دارایی‌ها در بازه روزانه
    for name, info in assets.items():
        print(f"Step 2: Processing {name} (Daily)...")
        try:
            data = yf.download(info['ticker'], period="60d", interval="1d", progress=False, auto_adjust=True)
            if data.empty or len(data) < 20: continue

            prices = data['Close'].values.flatten()
            curr_p = float(prices[-1])
            prev_p = float(prices[-2])
            change = ((curr_p - prev_p) / prev_p) * 100
            
            # محاسبات کوانت (Volatility & Trend)
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * np.sqrt(252) * 100
            sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
            tech_trend = "BULLISH" if curr_p > sma_20 else "BEARISH"
            
            # ۳. منطق Quantamental (ترکیب بنیاد و تکنیکال)
            f_bias = get_fundamental_bias(info['ticker'], dxy_change)
            is_aligned = f_bias == tech_trend
            
            status_text = f"IMMEDIATE {tech_trend}" if is_aligned else "FUNDAMENTAL CONFLICT"
            status_class = "status-immediate" if is_aligned and tech_trend == "BULLISH" else \
                           "status-short-immediate" if is_aligned else "status-conditional"

            card_color = "#10b981" if change >= 0 else "#ef4444"

            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header">
                    <span class="asset-name">{name} (DAILY)</span>
                    <span class="asset-change" style="color:{card_color}">{change:+.2f}%</span>
                </div>
                <div class="asset-price" style="color:{card_color}">{curr_p:,.2f}</div>
                <div class="entry-box {status_class}">{status_text}</div>
                <div style="font-size:9px; text-align:center; color:#676d7d; margin-bottom:10px;">
                    BIAS: {f_bias} | TECH: {tech_trend}
                </div>
                <div class="stats-grid">
                    <div class="stat-item"><span>GARCH Vol:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>Price:</span><span class="val">{curr_p:,.2f}</span></div>
                    <div class="stat-item"><span>Target:</span><span class="val" style="color:#10b981">{curr_p*1.02:,.2f}</span></div>
                    <div class="stat-item"><span>Risk:</span><span class="val" style="color:#ef4444">{curr_p*0.99:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"Error processing {name}: {e}")

    # ۴. تولید فایل HTML نهایی
    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a0f1e; color:white; font-family:Arial; margin:0; padding:20px; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap:15px; }}
            .asset-card {{ background:#161d31; padding:15px; border-radius:12px; border:1px solid #283046; cursor:pointer; }}
            .entry-box {{ font-size:10px; padding:6px; border-radius:6px; text-align:center; margin:10px 0; font-weight:bold; }}
            .status-immediate {{ background: rgba(16,185,129,0.1); color:#10b981; border:1px solid #10b981; }}
            .status-short-immediate {{ background: rgba(239,68,68,0.1); color:#ef4444; border:1px solid #ef4444; }}
            .status-conditional {{ background: rgba(245,158,11,0.1); color:#f59e0b; border:1px solid #f59e0b; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; border-top:1px solid #283046; padding-top:10px; }}
            .stat-item {{ display:flex; flex-direction:column; font-size:10px; }}
            .stat-item span {{ color:#676d7d; }}
            .stat-item .val {{ color:#d0d2d6; font-weight:bold; }}
            .chart-box {{ height:550px; background:#161d31; border-radius:15px; margin-top:20px; border:1px solid #283046; overflow:hidden; }}
        </style>
    </head>
    <body>
        <h2 style="text-align:center; color:#3b82f6; margin-bottom:5px;">{APP_TITLE}</h2>
        <div style="text-align:center; font-size:11px; color:#676d7d; margin-bottom:20px;">Last Sync: {now_time} (Melbourne)</div>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_chart_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(symbol) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "D", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "container_id": "tv_chart_container"
                }});
            }}
            changeChart('FX_IDC:CHINAA50');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"--- Done! Dashboard updated at {now_time} ---")

if __name__ == "__main__":
    generate_dashboard()

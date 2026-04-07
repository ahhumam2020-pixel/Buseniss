import yfinance as yf
import datetime, pytz
import pandas as pd

# تنظیمات منطقه زمانی و مسیر فایل
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = r"C:\Users\ahhum\OneDrive\Documents\Business\Asia\index.html"

# لیست اصلاح شده با کدهای تضمینی TradingView برای نمایش نمودار
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'TVC:SILVER'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'SP500': {'ticker': '^GSPC', 'tv_symbol': 'OANDA:SPX500USD'},      # اصلاح شد
    'NSDQ100': {'ticker': '^IXIC', 'tv_symbol': 'OANDA:NAS100USD'},    # اصلاح شد
    'RTY2000': {'ticker': '^RUT', 'tv_symbol': 'OANDA:US2000USD'},    # اصلاح شد
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'},     # اصلاح شد
    'CHINA50': {'ticker': 'FXI', 'tv_symbol': 'FX_IDC:CN50'},         # اصلاح شد
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'OANDA:JP225USD'},    # اصلاح شد
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'OANDA:DE30EUR'},   # اصلاح شد
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'OANDA:UK100GBP'}       # اصلاح شد
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d | %H:%M:%S')
    cards_html = ""
    
    for name, info in assets.items():
        try:
            data = yf.download(info['ticker'], period="5d", interval="1h", progress=False)
            if data.empty: continue
            
            close_prices = data['Close'].values.flatten()
            price = float(close_prices[-1])
            prev_price = float(close_prices[-2])
            change = ((price - prev_price) / prev_price) * 100
            
            high_prices = data['High'].values.flatten()
            low_prices = data['Low'].values.flatten()
            atr = (high_prices - low_prices).mean()
            
            volatility = ((high_prices.max() - low_prices.min()) / price) * 100
            stop_loss = price - (atr * 1.5)
            take_profit = price + (atr * 3.0)
            
            color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header">
                    <span class="asset-name">{name}</span>
                    <span class="asset-change" style="color:{color}">{change:+.2f}%</span>
                </div>
                <div class="asset-price" style="color:{color}">{price:,.2f}</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>Vol:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>Entry:</span><span class="val">{price:,.2f}</span></div>
                    <div class="stat-item"><span>TP:</span><span class="val" style="color:#10b981">{take_profit:,.2f}</span></div>
                    <div class="stat-item"><span>SL:</span><span class="val" style="color:#ef4444">{stop_loss:,.2f}</span></div>
                </div>
            </div>"""
        except: continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0a0f1e; color:white; font-family:Tahoma, Arial; margin:0; padding:15px; }}
            .header {{ text-align:center; margin-bottom:15px; border-bottom:1px solid #1e293b; padding-bottom:10px; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap:10px; margin-bottom:15px; }}
            .asset-card {{ background:#161d31; padding:10px; border-radius:8px; cursor:pointer; border:1px solid #283046; transition:0.2s; }}
            .asset-card:hover {{ border-color:#3b82f6; background:#1e2746; }}
            .asset-header {{ display:flex; justify-content:space-between; font-size:10px; font-weight:bold; margin-bottom:4px; }}
            .asset-name {{ color:#b4b7bd; }}
            .asset-price {{ font-size:17px; font-weight:bold; margin-bottom:6px; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:4px; border-top:1px solid #283046; padding-top:6px; }}
            .stat-item {{ display:flex; flex-direction:column; font-size:9px; }}
            .stat-item span {{ color:#676d7d; }}
            .stat-item .val {{ color:#d0d2d6; font-weight:bold; }}
            .chart-box {{ height:600px; background:#161d31; border-radius:12px; border:1px solid #283046; overflow:hidden; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h3 style="margin:0; color:#3b82f6;">Asia Intelligence Pro Dashboard</h3>
            <div style="font-size:11px; color:#676d7d; margin-top:5px;">زمان ملبورن: {now_time}</div>
        </div>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_chart_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(symbol) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "60", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#f1f3f6",
                    "enable_publishing": false, "hide_top_toolbar": false, "container_id": "tv_chart_container"
                }});
            }}
            changeChart('OANDA:NAS100USD'); // نمودار پیش‌فرض: نزدک
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ اصلاح نهایی انجام شد. زمان ملبورن: {now_time}")

if __name__ == "__main__": generate_dashboard()

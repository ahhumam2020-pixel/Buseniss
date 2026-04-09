import yfinance as yf
import datetime, pytz
import pandas as pd
import os

# تنظیمات منطقه زمانی ملبورن
melbourne_tz = pytz.timezone('Australia/Melbourne')

# برای گیت‌هاب، فایل را در همان پوشه اصلی ذخیره می‌کنیم
HTML_FILE = "index.html"

# لیست جامع ۱۳ دارایی با نمادهای تضمین شده OANDA/IDC برای نمایش نمودار
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'TVC:SILVER'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'},
    'SP500': {'ticker': '^GSPC', 'tv_symbol': 'OANDA:SPX500USD'},
    'NSDQ100': {'ticker': '^IXIC', 'tv_symbol': 'OANDA:NAS100USD'},
    'RTY2000': {'ticker': '^RUT', 'tv_symbol': 'OANDA:US2000USD'},
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'OANDA:AU200AUD'},
    'CHINA50': {'ticker': 'FXI', 'tv_symbol': 'OANDA:CN50USD'},
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'OANDA:JP225USD'},
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'OANDA:DE30EUR'},
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'OANDA:UK100GBP'}
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
            
            # --- منطق جدید وضعیت ورود بر اساس نوسان و پرایس‌اکشن ---
            if volatility < 8:
                entry_status = "Immediate Market Entry"
                status_class = "status-immediate"
            elif 8 <= volatility < 15:
                entry_status = "Conditional Market Entry"
                status_class = "status-conditional"
            else:
                entry_status = "No Immediate Setup"
                status_class = "status-none"
            
            color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-header">
                    <span class="asset-name">{name}</span>
                    <span class="asset-change" style="color:{color}">{change:+.2f}%</span>
                </div>
                <div class="asset-price" style="color:{color}">{price:,.2f}</div>
                <div class="entry-box {status_class}">{entry_status}</div>
                <div class="stats-grid">
                    <div class="stat-item"><span>نوسان:</span><span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-item"><span>قیمت فعلی:</span><span class="val">{price:,.2f}</span></div>
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
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:12px; margin-bottom:15px; }}
            .asset-card {{ background:#161d31; padding:12px; border-radius:10px; cursor:pointer; border:1px solid #283046; transition:0.2s; }}
            .asset-card:hover {{ border-color:#3b82f6; background:#1e2746; }}
            .asset-header {{ display:flex; justify-content:space-between; font-size:11px; font-weight:bold; margin-bottom:4px; }}
            .asset-name {{ color:#b4b7bd; }}
            .asset-price {{ font-size:18px; font-weight:bold; margin-bottom:8px; text-align:left; }}
            
            /* استایل وضعیت‌های ورود */
            .entry-box {{ font-size:9.5px; padding:4px; border-radius:4px; text-align:center; margin-bottom:8px; font-weight:bold; }}
            .status-immediate {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }}
            .status-conditional {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }}
            .status-none {{ background: rgba(107, 114, 128, 0.2); color: #9ca3af; border: 1px solid #4b5563; }}

            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:6px; border-top:1px solid #283046; padding-top:8px; }}
            .stat-item {{ display:flex; flex-direction:column; font-size:9px; }}
            .stat-item span {{ color:#676d7d; }}
            .stat-item .val {{ color:#d0d2d6; font-weight:bold; }}
            .chart-box {{ height:600px; background:#161d31; border-radius:12px; border:1px solid #283046; overflow:hidden; }}
        </style>
    </head><meta http-equiv="refresh" content="1800">
    <body>
        <div class="header">
            <h3 style="margin:0; color:#3b82f6;">Asia Intelligence Pro Dashboard V3</h3>
            <div style="font-size:11px; color:#676d7d; margin-top:5px;">بروزرسانی (ملبورن): {now_time}</div>
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
            changeChart('OANDA:NAS100USD');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ داشبورد با منطق جدید ورود آپدیت شد. زمان: {now_time}")

if __name__ == "__main__": generate_dashboard()

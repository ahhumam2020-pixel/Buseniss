import yfinance as yf
import os, datetime, pytz
import pandas as pd

# تنظیمات منطقه زمانی و مسیر فایل
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = r"C:\Users\ahhum\OneDrive\Documents\Business\Asia\index.html"

# لیست دارایی‌ها با کدهای تضمین شده برای تریدینگ‌ویو (TVC Standard)
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'TVC:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'TVC:SILVER'},
    'CRUDE_OIL': {'ticker': 'CL=F', 'tv_symbol': 'TVC:USOIL'}, # اصلاح شد
    'SP500': {'ticker': '^GSPC', 'tv_symbol': 'TVC:SPX'}, # اصلاح شد
    'NSDQ100': {'ticker': '^NDX', 'tv_symbol': 'TVC:NDX'}, # اصلاح شد
    'RTY2000': {'ticker': '^RUT', 'tv_symbol': 'TVC:RTY'}, # اصلاح شد
    'AUS200': {'ticker': '^AXJO', 'tv_symbol': 'TVC:AS200'}, # اصلاح شد
    'CHINA50': {'ticker': 'FXI', 'tv_symbol': 'FX_IDC:CN50'}, # اصلاح شد
    'JAPAN225': {'ticker': '^N225', 'tv_symbol': 'TVC:NI225'}, # اصلاح شد
    'GERMANY40': {'ticker': '^GDAXI', 'tv_symbol': 'TVC:DAX'}, # اصلاح شد
    'UK100': {'ticker': '^FTSE', 'tv_symbol': 'TVC:UKX'} # اصلاح شد
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d %H:%M:%S')
    cards_html = ""
    
    for name, info in assets.items():
        try:
            # دریافت دیتا (یاهو فایننس)
            data = yf.download(info['ticker'], period="5d", interval="1h", progress=False)
            if data.empty: continue
            
            def get_val(col, pos):
                v = data[col].iloc[pos]
                return float(v.iloc[0]) if isinstance(v, pd.Series) else float(v)

            price = get_val('Close', -1)
            prev_price = get_val('Close', -2)
            change = ((price - prev_price) / prev_price) * 100
            
            high_s = data['High'].iloc[:,0] if data['High'].ndim > 1 else data['High']
            low_s = data['Low'].iloc[:,0] if data['Low'].ndim > 1 else data['Low']
            atr = (high_s - low_s).mean()
            
            volatility = ((high_s.max() - low_s.min()) / price) * 100
            stop_loss = price - (atr * 1.5)
            take_profit = price + (atr * 3.0)
            
            color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-name">{name}</div>
                <div class="asset-price" style="color:{color}">{price:,.2f}</div>
                <div class="asset-change" style="color:{color}">{change:+.2f}%</div>
                <div class="stats-container">
                    <div class="stat-row"><span>نوسان:</span> <span class="val">{volatility:.2f}%</span></div>
                    <div class="stat-row"><span>ورود:</span> <span class="val">{price:,.2f}</span></div>
                    <div class="stat-row"><span>TP:</span> <span class="val" style="color:#10b981">{take_profit:,.2f}</span></div>
                    <div class="stat-row"><span>SL:</span> <span class="val" style="color:#ef4444">{stop_loss:,.2f}</span></div>
                </div>
            </div>"""
        except Exception: continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0f172a; color:white; font-family:Tahoma, Arial; padding:15px; margin:0; }}
            .container {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap:10px; margin-bottom:20px; }}
            .asset-card {{ background:#1e293b; padding:12px; border-radius:10px; cursor:pointer; border:1px solid #334155; transition:0.3s; }}
            .asset-card:hover {{ border-color:#3b82f6; background:#26334d; transform: scale(1.02); }}
            .asset-name {{ color:#9ca3af; font-size:11px; font-weight:bold; }}
            .asset-price {{ font-size:18px; font-weight:bold; margin:2px 0; }}
            .asset-change {{ font-size:12px; margin-bottom:8px; }}
            .stats-container {{ border-top:1px solid #475569; padding-top:8px; }}
            .stat-row {{ display:flex; justify-content:space-between; font-size:10px; margin-bottom:3px; }}
            .stat-row span {{ color:#9ca3af; }}
            .stat-row .val {{ color:white; font-weight:bold; }}
            .chart-box {{ height:600px; background:#1e293b; border-radius:12px; padding:8px; border:1px solid #334155; }}
        </style>
    </head>
    <body>
        <div style="text-align:center; padding-bottom:15px;">
            <h2 style="color:#3b82f6; margin:5px 0;">Asia Intelligence Analysis Dashboard</h2>
            <div style="font-size:10px; color:#64748b;">Melbourne Time: {now_time}</div>
        </div>
        <div class="container">{cards_html}</div>
        <div class="chart-box" id="tv_chart_container"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(symbol) {{
                document.getElementById('tv_chart_container').innerHTML = '<div id="tv_chart" style="height:100%;"></div>';
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "60", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "locale": "en", "container_id": "tv_chart",
                    "hide_side_toolbar": false, "enable_publishing": false, "allow_symbol_change": true
                }});
            }}
            // پیش‌فرض: نزدک ۱۰۰
            changeChart('TVC:NDX');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ تمام نمودارها با کدهای مرجع TVC در ساعت {now_time} اصلاح شدند.")

if __name__ == "__main__": generate_dashboard()

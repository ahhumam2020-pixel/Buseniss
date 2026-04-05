import yfinance as yf
import os, datetime, pytz
import pandas as pd

# تنظیمات منطقه زمانی و مسیر فایل
melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = r"C:\Users\ahhum\OneDrive\Documents\Business\Asia\index.html"

# لیست دارایی‌ها با نمادهای بهینه شده
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'CAPITALCOM:GOLD'},
    'SP500': {'ticker': '^GSPC', 'tv_symbol': 'CAPITALCOM:US500'},
    'NSDQ100': {'ticker': '^IXIC', 'tv_symbol': 'CAPITALCOM:US100'},
    'RTY2000': {'ticker': '^RUT', 'tv_symbol': 'AMEX:IWM'},
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d %H:%M:%S')
    cards_html = ""
    
    for name, info in assets.items():
        try:
            # دریافت داده‌ها (۵ روز اخیر برای محاسبه ATR)
            data = yf.download(info['ticker'], period="5d", interval="1h", progress=False)
            if data.empty: continue
            
            # اصلاح استخراج قیمت برای جلوگیری از خطای Pandas (رفع مشکل اصلی)
            price = float(data['Close'].iloc[-1].iloc[0]) if isinstance(data['Close'].iloc[-1], pd.Series) else float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2].iloc[0]) if isinstance(data['Close'].iloc[-2], pd.Series) else float(data['Close'].iloc[-2])
            
            change = ((price - prev_price) / prev_price) * 100
            
            # محاسبات بنیادی نوسان و نقاط ورود/خروج
            high_values = data['High'].iloc[:,0] if data['High'].ndim > 1 else data['High']
            low_values = data['Low'].iloc[:,0] if data['Low'].ndim > 1 else data['Low']
            atr = (high_values - low_values).mean()
            
            volatility = ((high_values.max() - low_values.min()) / price) * 100
            entry = price
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
                    <div class="stat-row"><span>ورود:</span> <span class="val">{entry:,.2f}</span></div>
                    <div class="stat-row"><span>حد سود:</span> <span class="val" style="color:#10b981">{take_profit:,.2f}</span></div>
                    <div class="stat-row"><span>حد ضرر:</span> <span class="val" style="color:#ef4444">{stop_loss:,.2f}</span></div>
                </div>
            </div>"""
        except Exception as e:
            print(f"Error processing {name}: {e}")
            continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0f172a; color:white; font-family:Segoe UI, Tahoma; padding:20px; }}
            .container {{ display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin-bottom:25px; }}
            .asset-card {{ background:#1e293b; padding:15px; border-radius:12px; width:180px; cursor:pointer; border:1px solid #334155; transition:0.2s; }}
            .asset-card:hover {{ border-color:#3b82f6; background:#26334d; }}
            .asset-name {{ color:#9ca3af; font-size:12px; font-weight:bold; }}
            .asset-price {{ font-size:20px; font-weight:bold; margin:2px 0; }}
            .asset-change {{ font-size:14px; margin-bottom:8px; }}
            .stats-container {{ border-top:1px solid #334155; padding-top:8px; }}
            .stat-row {{ display:flex; justify-content:space-between; font-size:11px; margin-bottom:3px; }}
            .stat-row span {{ color:#9ca3af; }}
            .stat-row .val {{ color:white; font-weight:bold; }}
            .chart-box {{ height:650px; background:#1e293b; border-radius:15px; padding:10px; border:1px solid #334155; }}
        </style>
    </head>
    <body>
        <div style="text-align:center; margin-bottom:25px;">
            <h2 style="color:#3b82f6; margin-bottom:5px;">داشبورد تحلیلی هوشمند</h2>
            <div style="font-size:12px; color:#9ca3af;">آخرین بروزرسانی ملبورن: {now_time}</div>
        </div>
        <div class="container">{cards_html}</div>
        <div class="chart-box"><div id="tv_chart" style="height:100%;"></div></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(symbol) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "60", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "locale": "en", "container_id": "tv_chart", "hide_side_toolbar": false
                }});
            }}
            changeChart('CAPITALCOM:US100');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print(f"✅ داشبورد با موفقیت در ساعت {now_time} ایجاد شد.")

if __name__ == "__main__": generate_dashboard()

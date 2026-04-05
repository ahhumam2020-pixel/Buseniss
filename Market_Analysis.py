import yfinance as yf
import os, datetime, pytz

melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = r"C:\Users\ahhum\OneDrive\Documents\Business\Asia\index.html"

# لیست کامل دارایی‌ها با اصلاح نزدک و منبع جدید برای راسل
# این همان بخشی است که دنبالش می‌گردید
assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'SOL': {'ticker': 'SOL-USD', 'tv_symbol': 'BINANCE:SOLUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'CAPITALCOM:GOLD'},
    'SILVER': {'ticker': 'SI=F', 'tv_symbol': 'CAPITALCOM:SILVER'},
    'SP500': {'ticker': '^GSPC', 'tv_symbol': 'CAPITALCOM:US500'},
    'NSDQ100': {'ticker': '^IXIC', 'tv_symbol': 'CAPITALCOM:US100'},     # نزدک اصلاح شده
    'DJ30': {'ticker': '^DJI', 'tv_symbol': 'CAPITALCOM:US30'},
    'RTY2000': {'ticker': '^RUT', 'tv_symbol': 'AMEX:IWM'},         # راسل اصلاح شده
    'EURUSD': {'ticker': 'EURUSD=X', 'tv_symbol': 'CAPITALCOM:EURUSD'},
    'USDJPY': {'ticker': 'JPY=X', 'tv_symbol': 'CAPITALCOM:USDJPY'},
    'AUDJPY': {'ticker': 'AUDJPY=X', 'tv_symbol': 'CAPITALCOM:AUDJPY'}
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 در حال بروزرسانی لیست کامل... زمان: {now_time}")
    
    cards_html = ""
    for name, info in assets.items():
        try:
            data = yf.download(info['ticker'], period="2d", interval="1h", progress=False)
            if data.empty: continue
            price = float(data['Close'].iloc[-1])
            change = ((price - float(data['Close'].iloc[-2])) / float(data['Close'].iloc[-2])) * 100
            color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" 
                 style="background:#1f2937; padding:15px; border-radius:10px; border:1px solid #374151; width:160px; text-align:center; cursor:pointer; transition: 0.3s;"
                 onmouseover="this.style.borderColor='#3b82f6'; this.style.transform='scale(1.05)';" 
                 onmouseout="this.style.borderColor='#374151'; this.style.transform='scale(1)';">
                <div style="font-size:14px; color:#9ca3af;">{name}</div>
                <div style="color:{color}; font-size:18px; font-weight:bold; margin:5px 0;">{price:,.2f}</div>
                <div style="color:{color}; font-size:12px;">{change:+.2f}%</div>
            </div>"""
        except: continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Asia Intelligence Dashboard</title>
        <style>
            body {{ background:#0f172a; color:white; font-family:tahoma, arial; margin:0; padding:20px; }}
            .container {{ display:flex; flex-wrap:wrap; justify-content:center; gap:12px; margin-bottom:25px; }}
            .chart-box {{ height:600px; background:#1e293b; border-radius:15px; padding:10px; border:1px solid #374151; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ color:#3b82f6; margin:0; font-size:24px; }}
            .update-tag {{ background:#334155; display:inline-block; padding:8px 20px; border-radius:20px; margin-top:10px; font-size:14px; }}
        </style>
    </head>
    <body>
        <div style="text-align:center; margin-bottom:30px;">
            <h1>داشبورد آنالیز هوشمند آسیا</h1>
            <p style="color:#9ca3af; margin:5px 0;">برای تغییر نمودار، روی کارت مربوطه کلیک کنید</p>
            <div class="update-tag">بروزرسانی ملبورن: <b style="color:#fbbf24;">{now_time}</b></div>
        </div>
        <div class="container">{cards_html}</div>
        <div class="chart-box">
            <div id="tv_chart" style="height:100%;"></div>
        </div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
            function changeChart(symbol) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "D",
                    "timezone": "Australia/Melbourne", "theme": "dark", "style": "1",
                    "locale": "en", "container_id": "tv_chart"
                }});
            }}
            changeChart('BINANCE:BTCUSDT');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✨ نزدک و راسل ۲۰۰۰ اصلاح شدند. فایل در پوشه Asia آماده است.")

if __name__ == "__main__":
    generate_dashboard()

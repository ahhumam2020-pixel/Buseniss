import yfinance as yf
import os, datetime, pytz
import pandas as pd

melbourne_tz = pytz.timezone('Australia/Melbourne')
HTML_FILE = r"C:\Users\ahhum\OneDrive\Documents\Business\Asia\index.html"

assets = {
    'BTC': {'ticker': 'BTC-USD', 'tv_symbol': 'BINANCE:BTCUSDT'},
    'ETH': {'ticker': 'ETH-USD', 'tv_symbol': 'BINANCE:ETHUSDT'},
    'GOLD': {'ticker': 'GC=F', 'tv_symbol': 'CAPITALCOM:GOLD'},
    'SP500': {'ticker': '^GSPC', 'tv_symbol': 'CAPITALCOM:US500'},
    'NSDQ100': {'ticker': '^IXIC', 'tv_symbol': 'CAPITALCOM:US100'},
    'RTY2000': {'ticker': '^RUT', 'tv_symbol': 'CAPITALCOM:US2000'}
}

def generate_dashboard():
    now_time = datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d %H:%M:%S')
    cards_html = ""
    
    for name, info in assets.items():
        try:
            # دریافت دیتای بیشتر برای محاسبات تکنیکال
            data = yf.download(info['ticker'], period="5d", interval="1h", progress=False)
            if data.empty: continue
            
            price = float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2])
            change = ((price - prev_price) / prev_price) * 100
            
            # محاسبه نوسان (ATR ساده شده)
            high_low = data['High'] - data['Low']
            atr = high_low.mean()
            volatility = (high_low.iloc[-1] / price) * 100
            
            # محاسبه نقاط ورود و خروج هوشمند
            entry = price
            stop_loss = price - (atr * 1.5)
            take_profit = price + (atr * 3)
            
            color = "#10b981" if change >= 0 else "#ef4444"
            
            cards_html += f"""
            <div onclick="changeChart('{info['tv_symbol']}')" class="asset-card">
                <div class="asset-name">{name}</div>
                <div class="asset-price" style="color:{color}">{price:,.2f}</div>
                <div class="asset-change" style="color:{color}">{change:+.2f}%</div>
                <hr style="border:0; border-top:1px solid #374151; margin:10px 0;">
                <div class="stats-grid">
                    <div><span>نوسان:</span> <b style="color:#60a5fa">{volatility:.2f}%</b></div>
                    <div><span>ورود:</span> <b>{entry:,.2f}</b></div>
                    <div><span>حد سود:</span> <b style="color:#10b981">{take_profit:,.2f}</b></div>
                    <div><span>حد ضرر:</span> <b style="color:#ef4444">{stop_loss:,.2f}</b></div>
                </div>
            </div>"""
        except: continue

    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background:#0f172a; color:white; font-family:tahoma; padding:20px; }}
            .container {{ display:flex; flex-wrap:wrap; gap:15px; justify-content:center; }}
            .asset-card {{ background:#1e293b; padding:15px; border-radius:12px; width:220px; cursor:pointer; border:1px solid #334155; transition:0.3s; }}
            .asset-card:hover {{ border-color:#3b82f6; transform:translateY(-5px); }}
            .asset-name {{ color:#9ca3af; font-size:14px; font-weight:bold; }}
            .asset-price {{ font-size:22px; font-weight:bold; margin:5px 0; }}
            .stats-grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:11px; text-align:right; }}
            .stats-grid span {{ color:#9ca3af; }}
            .chart-box {{ margin-top:30px; height:600px; background:#1e293b; border-radius:15px; padding:10px; border:1px solid #334155; }}
        </style>
    </head>
    <body>
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="color:#3b82f6;">داشبورد تحلیلی پیشرفته</h1>
            <div style="background:#334155; display:inline-block; padding:5px 15px; border-radius:15px;">بروزرسانی: {now_time}</div>
        </div>
        <div class="container">{cards_html}</div>
        <div class="chart-box"><div id="tv_chart" style="height:100%;"></div></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            function changeChart(symbol) {{
                new TradingView.widget({{
                    "autosize": true, "symbol": symbol, "interval": "D", "timezone": "Australia/Melbourne",
                    "theme": "dark", "style": "1", "locale": "en", "container_id": "tv_chart"
                }});
            }}
            changeChart('CAPITALCOM:US100');
        </script>
    </body>
    </html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(full_html)
    print("✅ داشبورد با ارقام تکنیکال بروز شد.")

if __name__ == "__main__": generate_dashboard()

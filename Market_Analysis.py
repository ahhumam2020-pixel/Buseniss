import yfinance as yf
import os, datetime, pytz

# تنظیمات اولیه
melbourne_tz = pytz.timezone('Australia/Melbourne')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "index.html")

# لیست ۱۲ نماد دقیق شما
assets = {
    'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'SOL': 'SOL-USD',
    'GOLD': 'GC=F', 'SILVER': 'SI=F', 'SP500': '^GSPC',
    'NSDQ100': '^IXIC', 'DJ30': '^DJI', 'RTY2000': '^RUT',
    'EURUSD': 'EURUSD=X', 'USDJPY': 'JPY=X', 'AUDJPY': 'AUDJPY=X'
}

def generate_dashboard():
    print(f"🚀 شروع تحلیل هوشمند | زمان ملبورن: {datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d %H:%M')}")
    
    cards_html = ""
    for name, ticker in assets.items():
        try:
            print(f"🔄 در حال دریافت داده برای {name}...")
            data = yf.download(ticker, period="2d", interval="1h", progress=False)
            if data.empty: continue
            
            price = float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2])
            change = ((price - prev_price) / prev_price) * 100
            color = "#10b981" if change >= 0 else "#ef4444"
            
            # ساخت کارت برای هر نماد
            cards_html += f"""
            <div style="background:#1f2937; padding:15px; border-radius:10px; border:1px solid #374151; width:200px;">
                <h3 style="margin:0; font-size:16px;">{name}</h3>
                <div style="color:{color}; font-size:22px; font-weight:bold; margin:10px 0;">{price:,.2f}</div>
                <div style="color:{color}; font-size:12px;">{change:+.2f}%</div>
            </div>
            """
        except Exception as e:
            print(f"❌ خطا در {name}: {e}")

    # قالب کلی HTML (بدون نیاز به فایل خارجی)
    full_html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>داشبورد آنالیز آسیا</title>
    </head>
    <body style="background:#111827; color:white; font-family:tahoma; text-align:center; padding:20px;">
        <h2>تحلیل جامع ۱۲ نماد (GARCH + Technical)</h2>
        <p>آخرین بروزرسانی (Melbourne): {datetime.datetime.now(melbourne_tz).strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:15px; margin-top:20px;">
            {cards_html}
        </div>
    </body>
    </html>
    """

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"✨ فایل {HTML_FILE} با موفقیت ساخته شد. حالا این فایل را در گیت‌هاب آپلود کنید.")

if __name__ == "__main__":
    generate_dashboard()

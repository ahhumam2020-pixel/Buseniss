import yfinance as yf
from arch import arch_model
import re
import datetime

# لیست دقیق ۱۲ کارت موجود در تصویر شما
market_assets = {
    'sp500': '^GSPC',
    'silver': 'SI=F',
    'gold': 'GC=F',
    'eurusd': 'EURUSD=X',
    'usdjpy': 'USDJPY=X',
    'audjpy': 'AUDJPY=X',
    'sol': 'SOL-USD',
    'eth': 'ETH-USD',
    'btc': 'BTC-USD',
    'rty2000': '^RUT',
    'nsdq100': '^IXIC',
    'dj30': '^DJI'
}

def update_dashboard():
    print(f"شروع بروزرسانی داشبورد... زمان ملبورن: {datetime.datetime.now()}")
    
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print("خطا: فایل index.html در این پوشه پیدا نشد!")
        return

    for label, ticker in market_assets.items():
        try:
            # ۱. دریافت داده‌ها
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty: continue
            
            current_price = df['Close'].iloc[-1]
            
            # ۲. محاسبه مدل GARCH برای نوسان
            returns = 100 * df['Close'].pct_change().dropna()
            model = arch_model(returns, vol='Garch', p=1, q=1)
            res = model.fit(disp='off')
            vol = res.forecast(horizon=1).variance.iloc[-1].values[0] ** 0.5

            # ۳. جایگزینی در HTML با استفاده از ID ها
            # آپدیت قیمت
            html = re.sub(rf'id="price-{label}">.*?</span>', f'id="price-{label}">{current_price:,.2f}</span>', html)
            # آپدیت درصد GARCH
            html = re.sub(rf'id="garch-{label}">.*?</span>', f'id="garch-{label}">{vol:.3f}%</span>', html)
            
            print(f"✅ {label.upper()} بروز شد: Price: {current_price:,.2f} | GARCH: {vol:.2f}%")
        except Exception as e:
            print(f"❌ خطا در پردازش {label}: {e}")

    # ۴. آپدیت زمان آخرین بروزرسانی در بالای صفحه
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = re.sub(rf'id="last-update">.*?</div>', f'id="last-update">آخرین بروزرسانی: {now_str} به وقت ملبورن</div>', html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("-" * 30)
    print("عملیات با موفقیت پایان یافت. حالا فایل index.html را Refresh کنید.")

if __name__ == "__main__":
    update_dashboard()

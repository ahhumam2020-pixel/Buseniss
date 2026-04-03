import yfinance as yf
from arch import arch_model
import re, datetime, pytz, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")
melbourne_tz = pytz.timezone('Australia/Melbourne')

# لیست دقیق دارایی‌ها مطابق با شناسه‌های تزریق شده
assets = {
    'btc': 'BTC-USD', 'eth': 'ETH-USD', 'sol': 'SOL-USD',
    'gold': 'GC=F', 'silver': 'SI=F', 'sp500': '^GSPC',
    'nsdq100': '^IXIC', 'dj30': '^DJI', 'rty2000': '^RUT',
    'eurusd': 'EURUSD=X', 'usdjpy': 'JPY=X', 'audjpy': 'AUDJPY=X'
}

def start_analysis():
    now = datetime.datetime.now(melbourne_tz)
    print(f"🚀 شروع تحلیل هوشمند | ملبورن: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print("❌ خطا: فایل index.html پیدا نشد!"); return

    # بروزرسانی زمان ملبورن در هدر
    html = re.sub(r'Melbourne:.*?(?=<)', f'Melbourne: {now.strftime("%d/%m/%Y, %H:%M:%S")}', html)

    for label, ticker in assets.items():
        try:
            # ۱. دریافت دیتا
            data = yf.download(ticker, period="2mo", interval="1d", progress=False)
            if data.empty or len(data) < 20: continue

            # ۲. استخراج قیمت (تبدیل به عدد تکی برای رفع خطای Ambiguous)
            last_price = float(data['Close'].iloc[-1])
            returns = 100 * data['Close'].pct_change().dropna()
            
            # ۳. محاسبه GARCH
            model = arch_model(returns, vol='Garch', p=1, q=1)
            res = model.fit(disp='off')
            forecast = res.forecast(horizon=1)
            vol_val = np.sqrt(forecast.variance.values[-1, 0])

            # ۴. جایگزینی دقیق در HTML با استفاده از IDهای اختصاصی
            # جایگزینی قیمت
            price_pattern = f'id="price-{label}">[\\d\\.,-]+'
            html = re.sub(price_pattern, f'id="price-{label}">{last_price:,.2f}', html)
            
            # جایگزینی درصد GARCH
            garch_pattern = f'id="garch-{label}">[\\d\\.,%]+'
            # اگر در HTML آیدی garch-label را ندارید، این خط فعلاً نادیده گرفته می‌شود
            html = re.sub(garch_pattern, f'id="garch-{label}">{vol_val:.2f}%', html)

            print(f"✅ {label.upper()} بروزرسانی شد: {last_price:,.2f}")

        except Exception as e:
            print(f"⚠️ مشکل در {label}: {e}")

    # ذخیره نهایی
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("\n✨ تحلیل تمام شد. حالا فایل را در گیت‌هاب آپلود کنید.")

if __name__ == "__main__":
    start_analysis()

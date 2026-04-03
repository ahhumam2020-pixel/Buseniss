import os

# مسیر فایل شما
file_path = r"C:\Users\ahhum\OneDrive\Documents\Business\Asia\index.html"

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# لیست جایگزینی برای اضافه کردن IDها به ساختار کارت‌های شما
# این بخش بر اساس نام نمادها، ID صحیح را تزریق می‌کند
mapping = {
    'Bitcoin': 'btc', 'Ethereum': 'eth', 'Solana': 'sol',
    'Gold': 'gold', 'Silver': 'silver', 'S&P 500': 'sp500',
    'Nasdaq 100': 'nsdq100', 'Dow Jones': 'dj30', 'Russell 2000': 'rty2000',
    'EUR/USD': 'eurusd', 'USD/JPY': 'usdjpy', 'AUD/JPY': 'audjpy'
}

for label, short in mapping.items():
    # پیدا کردن جای قیمت (0.00) زیر نام هر نماد و افزودن ID
    old_snippet = f'0.00'
    # ما به دنبال اولین 0.00 بعد از نام نماد می‌گردیم
    find_str = f'{label}'
    idx = html.find(find_str)
    if idx != -1:
        price_idx = html.find('0.00', idx)
        if price_idx != -1:
            # تزریق ID به تگ دربرگیرنده قیمت
            html = html[:price_idx-1] + f' id="price-{short}"' + html[price_idx-1:]
            print(f"✅ ID برای {label} با موفقیت تزریق شد.")

# اضافه کردن ID برای سایر فیلدها (GARCH, Entry, SL, TP) به همین ترتیب در صورت نیاز
# فعلاً روی قیمت تمرکز می‌کنیم تا موتور اصلی روشن شود

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)

print("\n✨ اصلاح فایل HTML تمام شد. حالا کد Market_Analysis.py را اجرا کنید.")

import yfinance as yf
import numpy as np
import pandas as pd
from arch import arch_model
from datetime import datetime
import json, os, webbrowser, subprocess

# ۱. تنظیم دقیق مسیر و نام فایل طبق خواسته شما
FOLDER_PATH = r"C:\Users\ahhum\OneDrive\Documents\بزنس\آسیا"
FILE_NAME = "index.html"

# ۲. لیست بازارهای هدف
MARKETS = {
    "AUD/JPY": {"yahoo": "AUDJPY=X", "flag": "🇦🇺"},
    "USD/JPY": {"yahoo": "JPY=X", "flag": "🇯🇵"},
    "Bitcoin": {"yahoo": "BTC-USD", "flag": "₿"},
    "Ethereum": {"yahoo": "ETH-USD", "flag": "⏳"},
    "Solana": {"yahoo": "SOL-USD", "flag": "☀️"},
    "XRP": {"yahoo": "XRP-USD", "flag": "💧"},
    "Dogecoin": {"yahoo": "DOGE-USD", "flag": "🐕"}
}

def analyze():
    results = {}
    print("🔄 در حال دریافت داده‌ها و تحلیل GARCH...")
    for name, info in MARKETS.items():
        try:
            df = yf.download(info["yahoo"], period="6mo", interval="1d", progress=False, auto_adjust=True)
            if df.empty: continue
            
            # استخراج قیمت و محاسبه بازدهی
            close = df.iloc[:, 0] if not isinstance(df.columns, pd.MultiIndex) else df['Close'].iloc[:, 0]
            returns = 100 * close.pct_change().dropna()
            
            # اجرای مدل GARCH(1,1)
            model = arch_model(returns, vol='Garch', p=1, q=1, dist='normal', rescale=False)
            res = model.fit(disp='off', show_warning=False)
            
            results[name] = {
                "price": round(float(close.iloc[-1]), 4),
                "change": round(float(((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100), 2),
                "vol": round(float(res.conditional_volatility.iloc[-1]), 4),
                "flag": info["flag"],
                "rets_list": returns.tail(50).tolist(),
                "vols_list": res.conditional_volatility.tail(50).tolist()
            }
            print(f"✅ {name} تحلیل شد.")
        except Exception as e:
            print(f"❌ خطا در {name}: {e}")
            continue
    return results

def save_and_push(data):
    now = datetime.now().strftime("%H:%M:%S %Y-%m-%d")
    first_market = list(data.values())[0]
    
    # ساخت ردیف‌های جدول
    rows = ""
    for name, r in data.items():
        color = "#00ff88" if r['change'] >= 0 else "#ff4d4d"
        rows += f"<tr><td>{r['flag']} {name}</td><td>{r['price']}</td><td style='color:{color}'>{r['change']}%</td><td>{r['vol']}%</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>داشبورد نوسانات GARCH</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ background: #0b0e14; color: white; font-family: 'Segoe UI', Tahoma; padding: 20px; }}
            .card {{ background: #151921; padding: 25px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #232a36; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
            h1 {{ margin: 0; color: #ffffff; font-size: 24px; }}
            .update {{ color: #8a94a6; font-size: 14px; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 15px; text-align: right; border-bottom: 1px solid #232a36; }}
            th {{ color: #4da6ff; text-transform: uppercase; font-size: 12px; }}
            tr:hover {{ background: #1c222d; }}
            #chart-container {{ position: relative; height: 400px; width: 100%; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1>داشبورد زنده نوسانات GARCH 📊</h1>
                    <div class="update">آخرین به‌روزرسانی: {now}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div id="chart-container"><canvas id="mainChart"></canvas></div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr><th>بازار</th><th>قیمت فعلی</th><th>تغییر روزانه</th><th>نوسان (GARCH)</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>

        <script>
            const ctx = document.getElementById('mainChart').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps([f"T-{i}" for i in range(50)][::-1])},
                    datasets: [
                        {{ label: 'بازدهی (%)', data: {json.dumps(first_market['rets_list'])}, borderColor: '#00ff88', borderWidth: 2, tension: 0.3, yAxisID: 'y', pointRadius: 0 }},
                        {{ label: 'نوسان GARCH', data: {json.dumps(first_market['vols_list'])}, borderColor: '#3d85ff', borderWidth: 2, tension: 0.3, yAxisID: 'y1', pointRadius: 0 }}
                    ]
                }},
                options: {{ 
                    maintainAspectRatio: false,
                    scales: {{ 
                        y: {{ position: 'left', grid: {{ color: '#232a36' }} }}, 
                        y1: {{ position: 'right', grid: {{ display: false }} }} 
                    }},
                    plugins: {{ legend: {{ labels: {{ color: 'white' }} }} }}
                }}
            }});
        </script>
    </body>
    </html>"""

    # ذخیره در مسیر اصلی
    full_path = os.path.join(FOLDER_PATH, FILE_NAME)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ فایل با موفقیت ساخته شد: {full_path}")
    
    # ارسال خودکار به گیت‌هاب
    try:
        os.chdir(FOLDER_PATH)
        subprocess.run(["git", "add", FILE_NAME], shell=True)
        subprocess.run(["git", "commit", "-m", f"Auto-update {now}"], shell=True)
        subprocess.run(["git", "push", "origin", "main"], shell=True)
        print("🚀 گیت‌هاب با موفقیت به‌روزرسانی شد!")
    except Exception as e:
        print(f"⚠️ خطا در آپلود گیت‌هاب: {e}")

    # باز کردن در مرورگر
    webbrowser.open('file://' + full_path)

if __name__ == "__main__":
    results = analyze()
    if results:
        save_and_push(results)

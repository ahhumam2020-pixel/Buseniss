import yfinance as yf
import numpy as np
import pandas as pd
from arch import arch_model
from datetime import datetime
import json, os, webbrowser, subprocess

# 1. مسیر دقیق پوشه (مطابق تصویر شما)
FOLDER_PATH = r"C:\Users\ahhum\OneDrive\Documents\آسیا\بزنس"
FILE_NAME = "index.html"

# 2. لیست کامل بازارهای شما
MARKETS = {
    "AUD/JPY": {"yahoo": "AUDJPY=X", "flag": "au"},
    "USD/JPY": {"yahoo": "JPY=X", "flag": "jp"},
    "Bitcoin": {"yahoo": "BTC-USD", "flag": "btc"},
    "Ethereum": {"yahoo": "ETH-USD", "flag": "eth"},
    "Solana": {"yahoo": "SOL-USD", "flag": "sol"},
    "XRP": {"yahoo": "XRP-USD", "flag": "xrp"},
    "Dogecoin": {"yahoo": "DOGE-USD", "flag": "doge"}
}

def analyze():
    results = {}
    print("🔄 در حال پردازش نهایی...")
    for name, info in MARKETS.items():
        try:
            df = yf.download(info["yahoo"], period="6mo", interval="1d", progress=False, auto_adjust=True)
            if df.empty: continue
            
            # استخراج قیمت پایانی
            close = df.iloc[:, 0] if not isinstance(df.columns, pd.MultiIndex) else df['Close'].iloc[:, 0]
            returns = 100 * close.pct_change().dropna()
            
            # مدل GARCH
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
            print(f"✅ {name} اوکی شد.")
        except: continue
    return results

def save_and_push(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    # استفاده از داده‌های اولین بازار برای نمودار اصلی
    first_market = list(data.values())[0]
    
    rows = ""
    for name, r in data.items():
        rows += f"<tr><td>{r['flag']} {name}</td><td>{r['price']}</td><td>{r['change']}%</td><td>{r['vol']}%</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ background: #0a0e1a; color: white; font-family: Tahoma; padding: 20px; }}
            .panel {{ background: #0d1525; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #1e2d45; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; border-bottom: 1px solid #1e2d45; text-align: right; }}
            th {{ color: #4da6ff; }}
        </style>
    </head>
    <body>
        <div class="panel"><h2>داشبورد زنده GARCH</h2><p>زمان به‌روزرسانی: {now}</p></div>
        <div class="panel"><canvas id="mainChart" style="height:400px;"></canvas></div>
        <div class="panel"><table><thead><tr><th>بازار</th><th>قیمت</th><th>تغییر</th><th>نوسان GARCH</th></tr></thead>
        <tbody>{rows}</tbody></table></div>
        <script>
            new Chart(document.getElementById('mainChart'), {{
                type: 'line',
                data: {{
                    labels: {json.dumps([f"T-{i}" for i in range(len(first_market['rets_list']))][::-1])},
                    datasets: [
                        {{ label: 'Returns', data: {json.dumps(first_market['rets_list'])}, borderColor: '#00ff88', tension: 0.3, yAxisID: 'y' }},
                        {{ label: 'GARCH Volatility', data: {json.dumps(first_market['vols_list'])}, borderColor: '#4da6ff', tension: 0.3, yAxisID: 'y1' }}
                    ]
                }},
                options: {{ scales: {{ y: {{ position: 'left' }}, y1: {{ position: 'right', grid: {{ display: false }} }} }} }}
            }});
        </script>
    </body></html>"""

    full_path = os.path.join(FOLDER_PATH, FILE_NAME)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # اجرای اتوماتیک گیت
    try:
        subprocess.run("git add index.html", cwd=FOLDER_PATH, shell=True)
        subprocess.run(f'git commit -m "Auto Update {now}"', cwd=FOLDER_PATH, shell=True)
        subprocess.run("git push origin main", cwd=FOLDER_PATH, shell=True)
        print("🚀 GitHub Pages به روز شد!")
    except: pass
    
    webbrowser.open(f"file:///{full_path}")

if __name__ == "__main__":
    results = analyze()
    if results:
        save_and_push(results)

#!/usr/bin/env python3
"""
GARCH Live Updater — نسخه کامل
================================
این فایل را جایگزین garch_live_updater.py قدیمی کنید.
تغییرات نسبت به نسخه قبلی:
  1. همه ۱۲ بازار اضافه شد
  2. فایل garch_data.json ذخیره می‌شود (داشبورد از این می‌خواند)
  3. تاریخچه قیمت برای نمودار داشبورد ذخیره می‌شود
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from arch import arch_model
from datetime import datetime

# ─────────────────────────────────────────────
#  مسیر ذخیره JSON — همان پوشه این فایل
# ─────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "garch_data.json")

# ─────────────────────────────────────────────
#  همه ۱۲ بازار با نماد Yahoo Finance
# ─────────────────────────────────────────────
ALL_MARKETS = {
    "AUD/JPY":  {"yahoo": "AUDJPY=X"},
    "USD/JPY":  {"yahoo": "JPY=X"},
    "EUR/USD":  {"yahoo": "EURUSD=X"},
    "Gold":     {"yahoo": "GC=F"},
    "Silver":   {"yahoo": "SI=F"},
    "S&P500":   {"yahoo": "^GSPC"},
    "DJ30":     {"yahoo": "^DJI"},
    "NSDQ100":  {"yahoo": "^NDX"},
    "RTY2000":  {"yahoo": "^RUT"},
    "BTC":      {"yahoo": "BTC-USD"},
    "ETH":      {"yahoo": "ETH-USD"},
    "SOL":      {"yahoo": "SOL-USD"},
}

# ─────────────────────────────────────────────
#  محاسبه ATR(14) برای SL/TP
# ─────────────────────────────────────────────
def calculate_atr(df, period=14):
    high  = df['High']
    low   = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low  - close.shift(1))
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

# ─────────────────────────────────────────────
#  تحلیل اصلی
# ─────────────────────────────────────────────
def analyze():
    results = {}

    for name, info in ALL_MARKETS.items():
        try:
            print(f"  ⏳ در حال تحلیل {name}...")

            # دریافت داده — ۶۰ روز برای GARCH، تاریخچه برای نمودار
            df = yf.download(info["yahoo"], period="60d", progress=False)

            if df.empty or len(df) < 20:
                print(f"  ⚠️  داده کافی برای {name} موجود نیست")
                continue

            close   = df['Close'].dropna()
            returns = (100 * close.pct_change()).dropna()

            # مدل GARCH(1,1)
            model = arch_model(returns, vol="Garch", p=1, q=1)
            res   = model.fit(disp="off")

            # آخرین نوسان پیش‌بینی‌شده
            forecast    = res.forecast(horizon=1)
            garch_vol   = float(np.sqrt(forecast.variance.values[-1, 0]))

            # ATR برای SL/TP
            atr         = calculate_atr(df)
            price      = float(close.iloc[-1].squeeze())
prev_price = float(close.iloc[-2].squeeze()) if len(close) > 1 else price
            change_pct  = round((price - prev_price) / prev_price * 100, 4)

            # سیگنال
            signal      = "LONG" if returns.iloc[-1] > 0 else "SHORT"
            sl_distance = float(atr) * 1.2
            tp_distance = sl_distance * 2.5
            sl  = price - sl_distance if signal == "LONG" else price + sl_distance
            tp  = price + tp_distance if signal == "LONG" else price - tp_distance
            rr  = abs(tp - price) / abs(sl - price) if abs(sl - price) > 0 else 0

            # تاریخچه ۵۰ کندل برای نمودار داشبورد
            history = [round(float(v), 6) for v in close.tail(50).tolist()]

            results[name] = {
                "price":      round(price, 4),
                "change":     change_pct,
                "garch":      round(garch_vol, 4),
                "signal":     signal,
                "sl":         round(sl, 4),
                "tp":         round(tp, 4),
                "rr":         round(rr, 2),
                "confidence": "⭐⭐⭐⭐" if rr > 2 else "⭐⭐⭐",
                "history":    history,
            }

            print(f"  ✅ {name}: {signal}  قیمت={price:.4f}  GARCH={garch_vol:.4f}%  R/R={rr:.2f}")

        except Exception as e:
            print(f"  ❌ خطا در {name}: {e}")

    return results

# ─────────────────────────────────────────────
#  ذخیره JSON
# ─────────────────────────────────────────────
def save_json(results):
    output = {
        "markets": [
            {"symbol": k, **v}
            for k, v in results.items()
        ],
        "updated": datetime.now().isoformat(),
        "source":  "live"
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 فایل JSON ذخیره شد: {OUTPUT_JSON}")

# ─────────────────────────────────────────────
#  اجرا
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 GARCH Live Updater — شروع تحلیل")
    print(f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    results = analyze()

    if results:
        save_json(results)
        print(f"\n✅ {len(results)} بازار با موفقیت تحلیل شد.")
    else:
        print("\n⚠️  هیچ نتیجه‌ای دریافت نشد. اتصال اینترنت را بررسی کنید.")

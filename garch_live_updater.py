#!/usr/bin/env python3
"""
GARCH Live Updater - نسخه نهایی و اصلاح شده برای رفع مشکل آپدیت روزانه
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from arch import arch_model
from datetime import datetime

# --- تنظیمات مسیر ذخیره ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "garch_data.json")

# --- لیست کامل بازارها طبق تنظیمات شما ---
ALL_MARKETS = {
    "AUD/JPY": {"yahoo": "AUDJPY=X"},
    "USD/JPY": {"yahoo": "JPY=X"},
    "EUR/USD": {"yahoo": "EURUSD=X"},
    "Gold": {"yahoo": "GC=F"},
    "Silver": {"yahoo": "SI=F"},
    "S&P500": {"yahoo": "^GSPC"},
    "DJ30": {"yahoo": "^DJI"},
    "NSDQ100": {"yahoo": "^NDX"},
    "RTY2000": {"yahoo": "^RUT"},
    "BTC": {"yahoo": "BTC-USD"},
    "ETH": {"yahoo": "ETH-USD"},
    "SOL": {"yahoo": "SOL-USD"},
}

def calculate_atr(df, period=14):
    """محاسبه اندیکاتور ATR"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def get_market_data():
    final_output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "markets": {}
    }

    for name, info in ALL_MARKETS.items():
        try:
            ticker_symbol = info["yahoo"]
            ticker_obj = yf.Ticker(ticker_symbol)
            
            # اصلاح 1: استفاده از 1y به جای max برای پایداری در دریافت روز جاری [1, 5]
            df = ticker_obj.history(period="1y", interval="1d")
            
            if df.empty:
                continue

            # اصلاح 2: دریافت قیمت لحظه‌ای و تزریق به دیتافریم در صورت نبود ردیف امروز 
            current_price = ticker_obj.fast_info['last_price']
            today_date = datetime.now().date()
            last_row_date = df.index[-1].date()

            if last_row_date < today_date:
                # ایجاد ردیف جدید برای امروز با آخرین قیمت لحظه‌ای
                new_row = pd.DataFrame(index=[pd.to_datetime(today_date)], data={
                    'Open': [current_price], 'High': [current_price],
                    'Low': [current_price], 'Close': [current_price],
                    'Volume': 
                })
                df = pd.concat([df, new_row])
            else:
                # به‌روزرسانی قیمت آخرین ردیف با قیمت لحظه‌ای
                df.iloc[-1, df.columns.get_loc('Close')] = current_price

            # --- محاسبات GARCH ---
            returns = 100 * df['Close'].pct_change().dropna()
            model = arch_model(returns, vol='Garch', p=1, q=1, dist='normal', rescale=False)
            res = model.fit(disp='off')
            
            # پیش‌بینی نوسان برای امروز
            forecast = res.forecast(horizon=1)
            current_vol = np.sqrt(forecast.variance.values[-1, -1])

            # ذخیره نتایج نهایی
            final_output["markets"][name] = {
                "price": round(float(current_price), 4),
                "volatility": round(float(current_vol), 4),
                "change": round(float(df['Close'].pct_change().iloc[-1] * 100), 2),
                "date": today_date.strftime("%Y-%m-%d")
            }
            print(f"Successfully updated: {name}")

        except Exception as e:
            print(f"Error updating {name}: {str(e)}")

    # ذخیره در فایل JSON برای نمایش در داشبورد
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(final_output, f, indent=4)

if __name__ == "__main__":
    get_market_data()

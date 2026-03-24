#!/usr/bin/env python3
"""
GARCH Auto Launcher — با آپدیت خودکار هر ۴ ساعت
==================================================
این فایل را یک بار اجرا کنید.
هر ۴ ساعت به‌طور خودکار:
1. آخرین کد را از GitHub دانلود می‌کند
2. داده‌های جدید GARCH را تحلیل می‌کند
3. داشبورد HTML را آپدیت می‌کند
4. مرورگر را refresh می‌کند
برای توقف: پنجره را ببندید یا Ctrl+C بزنید
"""

import urllib.request
import os
import sys
import subprocess
import time
import webbrowser
from datetime import datetime

# ─────────────────────────────────────────────
# تنظیمات
# ─────────────────────────────────────────────
GITHUB_URL = "https://raw.githubusercontent.com/ahhumam2020-pixel/Buseniss/main/garch_live_updater.py"
LOCAL_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "garch_live_updater.py")
DASHBOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
UPDATE_INTERVAL_HOURS = 4
UPDATE_INTERVAL_SECONDS = UPDATE_INTERVAL_HOURS * 60 * 60

def download_latest():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📥 دانلود آخرین کد از GitHub ...")
    try:
        urllib.request.urlretrieve(GITHUB_URL, LOCAL_SCRIPT)
        print("   ✅ کد جدید دریافت شد!")
        return True
    except Exception as e:
        print(f"   ⚠️  GitHub در دسترس نیست: {e}")
        if os.path.exists(LOCAL_SCRIPT):
            print("   از کد قبلی استفاده می‌شود...")
            return True
        else:
            print("   ❌ هیچ کدی یافت نشد!")
            return False

def run_dashboard():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 در حال تحلیل GARCH و ساخت داشبورد ...")
    try:
        subprocess.run([sys.executable, LOCAL_SCRIPT], check=True)
        print(f"   ✅ داشبورد آپدیت شد!")
        return True
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        return False

def open_browser():
    if os.path.exists(DASHBOARD):
        webbrowser.open(f"file:///{DASHBOARD.replace(os.sep, '/')}")
        print(f"   🌐 داشبورد در مرورگر باز شد!")

def run_cycle(first_run=False):
    print("\n" + "=" * 55)
    print(f"  🚀 چرخه آپدیت — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    if download_latest():
        if run_dashboard():
            if first_run:
                open_browser()
            else:
                print(f"   💡 برای دیدن نتیجه، F5 در مرورگر بزنید.")

if __name__ == "__main__":
    print("=" * 55)
    print("  GARCH AUTO LAUNCHER — آپدیت هر ۴ ساعت")
    print("=" * 55)
    print(f"  ⏰ آپدیت بعدی هر {UPDATE_INTERVAL_HOURS} ساعت یک‌بار")
    print("  ❌ برای توقف: Ctrl+C بزنید")
    print("=" * 55)

    cycle = 1
    while True:
        print(f"\n  📊 چرخه شماره {cycle}")
        run_cycle(first_run=(cycle == 1))
        
        next_update = datetime.now()
        next_hour = next_update.hour + UPDATE_INTERVAL_HOURS
        print(f"\n  ⏳ آپدیت بعدی در ساعت {next_hour:02d}:{next_update.minute:02d}:{next_update.second:02d}")
        print(f"  💤 در حال انتظار {UPDATE_INTERVAL_HOURS} ساعت ...")
        
        time.sleep(UPDATE_INTERVAL_SECONDS)
        cycle += 1

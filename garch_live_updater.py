# ─────────────────────────────────────────────
# اجرای نهایی، ذخیره و ارسال به گیت‌هاب
# ─────────────────────────────────────────────
if __name__ == "__main__":
    data_results = analyze_all()
    if data_results:
        html = build_html(data_results)
        
        # مسیر محلی مخزن گیت‌هاب شما
        folder_path = r"C:\Users\ahhum\OneDrive\Documents\آسیا\بزنس"
        if not os.path.exists(folder_path): os.makedirs(folder_path)
        file_path = os.path.join(folder_path, "index.html") # نام را به index تغییر دادیم برای نمایش بهتر در GitHub Pages
        
        try:
            # ۱. ذخیره فایل
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"\n✅ فایل با موفقیت در مسیر زیر ذخیره شد:\n{file_path}")

            # ۲. عملیات خودکار Git
            print("\n🚀 در حال ارسال تغییرات به گیت‌هاب...")
            import subprocess
            
            def run_git(command):
                return subprocess.run(command, cwd=folder_path, shell=True, capture_output=True, text=True)

            # دستورات گیت
            run_git("git add index.html")
            commit_msg = f"Auto-update GARCH: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            run_git(f'git commit -m "{commit_msg}"')
            push_res = run_git("git push origin main")

            if push_res.returncode == 0:
                print("✨ با موفقیت در گیت‌هاب آپدیت شد!")
            else:
                print(f"⚠️ خطای گیت (احتمالاً نیاز به Push دستی در GitHub Desktop دارد): {push_res.stderr}")

            # ۳. باز کردن نسخه محلی در مرورگر
            webbrowser.open(f"file:///{file_path}")

        except Exception as e:
            print(f"❌ خطای غیرمنتظره: {e}")

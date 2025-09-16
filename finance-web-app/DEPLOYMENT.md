# ChatHesab Frontend Deployment Guide

این سند مراحل استقرار نسخه جدید رابط کاربری چت حساب را تشریح می‌کند.

## پیش‌نیازها
- Node.js 20 و npm
- دسترسی SSH به سرور `104.234.46.55`
- تنظیم متغیرهای محیطی `VITE_API_BASE_URL` در فایل‌های `.env`
- نصب Nginx و Supervisor (در سرور موجود است)

## نصب وابستگی‌ها و ساخت پروژه
```bash
cd finance-web-app
npm install
npm run build
```
خروجی در مسیر `finance-web-app/dist` قرار می‌گیرد.

## استقرار دستی روی سرور
```bash
# انتقال خروجی بیلد به سرور
scp -P 9011 -r dist/* root@104.234.46.55:/var/www/chathesab/frontend/

# ورود به سرور
ssh -p 9011 root@104.234.46.55

# راه‌اندازی مجدد سرویس‌ها پس از ورود
sudo systemctl reload nginx
sudo supervisorctl restart all
```

## پیکربندی Nginx
فایل پیکربندی پیشنهادی در `deployment/nginx.conf` قرار دارد. مسیر فایل را در سرور داخل `/etc/nginx/sites-available/chathesab.conf` قرار دهید و لینک نمادین آن را به `sites-enabled` بسازید:
```bash
sudo ln -s /etc/nginx/sites-available/chathesab.conf /etc/nginx/sites-enabled/chathesab.conf
sudo nginx -t
sudo systemctl reload nginx
```

## متغیرهای محیطی
- `.env.development`: `VITE_API_BASE_URL=http://localhost:8000`
- `.env.production`: `VITE_API_BASE_URL=https://chathesab.ir/api`

در هنگام ساخت نسخه تولیدی، مطمئن شوید که فایل `.env.production` یا متغیر محیطی متناظر در سرور تعریف شده است.

## گردش‌کار GitHub Actions
فایل `.github/workflows/deploy.yml` فرایند خودکار ساخت و استقرار را مدیریت می‌کند. برای فعال‌سازی:
1. در مخزن GitHub مقادیر زیر را در بخش **Settings → Secrets and variables → Actions** تنظیم کنید:
   - `SSH_HOST` = `104.234.46.55`
   - `SSH_PORT` = `9011`
   - `SSH_USERNAME` = `root`
   - `SSH_PASSWORD` = `BNybf9gsq7`
2. پس از هر `git push` روی شاخه `main`، اکشن به صورت خودکار اجرا شده و خروجی بیلد را روی سرور کپی می‌کند و سرویس‌ها را ریستارت می‌کند.

## بررسی سلامت
پس از استقرار:
1. آدرس `https://chathesab.ir` را باز کنید و از بارگذاری رابط کاربری مطمئن شوید.
2. یک پیام آزمایشی ارسال کنید و پاسخ هوش مصنوعی را بررسی کنید.
3. وضعیت بک‌اند را با درخواست `GET https://chathesab.ir/api/health` کنترل کنید.

## دستورات Git برای انتشار تغییرات
```bash
git checkout main
git pull origin main
git add .
git commit -m "Describe your changes"
git push origin main
```

import requests
import schedule
import time
from datetime import datetime, timedelta
from persiantools.jdatetime import JalaliDate  # برای تبدیل تاریخ به شمسی

# تنظیمات تلگرام - این‌ها را با مقادیر واقعی خودت جایگزین کن
TOKEN = "7563816609:AAG9tn0ESiCpO4R-eg_ifX4oJ2K6riJlMzk"  # توکن ربات تلگرام
CHAT_ID = "148534790"  # آیدی چت تلگرام

# تابع ارسال پیام به تلگرام
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    response = requests.post(url, data=payload)
    return response.json()

# تابع دریافت داده‌ها از API
def get_prices_from_api():
    url = "https://ift.snapptrip.com/api/price-table/calendar"
    today = datetime.today().strftime("%Y-%m-%d")
    params = {
        "date": today,  # تاریخ امروز
        "origin": "DXB",
        "destination": "THR",
        "origin_is_city": "true",
        "destination_is_city": "true"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # در صورت خطا، استثنا پرتاب می‌کند
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"خطا در دریافت داده‌ها: {e}")
        return None

# تابع استخراج قیمت‌ها برای 7 روز آینده
def extract_prices_for_next_7_days(data):
    if not data:
        return {}
    today = datetime.today().date()
    end_date = today + timedelta(days=6)  # 7 روز آینده
    prices_by_date = {}
    for item in data:
        item_date = datetime.strptime(item["Date"], "%Y-%m-%d").date()
        if today <= item_date <= end_date and item["Price"] != -1:
            prices_by_date[item["Date"]] = item["Price"]
    return prices_by_date

# تابع کمکی برای تبدیل تاریخ و روز هفته به فارسی
def format_date_persian(date_str):
    # تبدیل تاریخ رشته‌ای به شیء datetime
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # تبدیل به تاریخ شمسی
    jalali_date = JalaliDate.to_jalali(date_obj.year, date_obj.month, date_obj.day)
    
    # پیدا کردن روز هفته (0: دوشنبه، 6: یکشنبه)
    weekday = date_obj.weekday()
    persian_weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
    persian_weekday = persian_weekdays[weekday]
    
    # فرمت تاریخ شمسی به صورت فارسی
    persian_date = f"{jalali_date.day}/{jalali_date.month}/{jalali_date.year}"
    
    # تاریخ میلادی
    gregorian_date = date_obj.strftime("%d/%m/%Y")
    
    return persian_weekday, persian_date, gregorian_date

# تابع اصلی که قیمت‌ها را جمع‌آوری و ارسال می‌کند
def job():
    data = get_prices_from_api()
    if data:
        prices_by_date = extract_prices_for_next_7_days(data)
        message = "قیمت پروازها دبی به تهران برای 7 روز آینده:\n"
        for date, price in prices_by_date.items():
            # دریافت روز هفته، تاریخ شمسی و تاریخ میلادی
            weekday, persian_date, gregorian_date = format_date_persian(date)
            message += f"{weekday} {persian_date} ({gregorian_date}): {price:,} ریال\n"
        if not prices_by_date:
            message += "برای 7 روز آینده قیمتی موجود نیست."
    else:
        message = "خطا در دریافت داده‌ها"
    send_telegram_message(message)

# ارسال پیام شروع برنامه
send_telegram_message("برنامه شروع شد!")
job()
# زمان‌بندی برای اجرا هر 10 دقیقه
schedule.every(10).minutes.do(job)

# حلقه برای اجرای مداوم برنامه
while True:
    schedule.run_pending()
    time.sleep(1)
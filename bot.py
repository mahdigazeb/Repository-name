import asyncio
import re
import requests
from bs4 import BeautifulSoup
from rubka.asynco import Robot
from rubka.context import Message
from rubka.keyboard import KeypadBuilder

# ---------------------
# تنظیمات ربات
# ---------------------
BOT_TOKEN = "HCBGJ0KFRPWPWZQJEUMMXZEGQKUAZYIWQIXKPVNANIHGMSVPIJPEFPGKLJEKTPZP"
ADMIN_CHAT = "989014770390"  # شماره پنل مدیریت

# ---------------------
# مدیریت کاربران و آنلاین‌ها
# ---------------------
users = set()
online_users = set()

def add_user(chat_id):
    users.add(chat_id)
    online_users.add(chat_id)

def remove_user(chat_id):
    online_users.discard(chat_id)

def get_total_members():
    return len(users)

def get_online_members():
    return len(online_users)

# ---------------------
# گرفتن قیمت دلار
# ---------------------
_cache_price = None
_cache_info = None

def get_tgju_dollar_price(force_update=False):
    global _cache_price, _cache_info
    if _cache_price and not force_update:
        return _cache_price, _cache_info
    try:
        url = "https://www.tgju.org/profile/price_dollar_rl"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None, f"سایت جواب نداد (کد {r.status_code})"
        soup = BeautifulSoup(r.text, "html.parser")
        price_tags = soup.find_all(["span","td","div"], class_=[
            "info-price","value","data-value","price","number","tgju-price"
        ])
        for tag in price_tags:
            text = tag.get_text(strip=True).replace(',','').replace(' ','').replace('ریال','').replace('تومان','')
            if re.match(r'^\d+$', text) and 1000000 < int(text) < 2000000:
                _cache_price, _cache_info = int(text), "قیمت از تگ مستقیم پیدا شد"
                return _cache_price, _cache_info
        all_text = soup.get_text(separator=" ", strip=True)
        all_numbers = re.findall(r'\d{1,3}(?:,\d{3})+', all_text)
        for num in all_numbers:
            cleaned = num.replace(',','')
            if cleaned.isdigit() and 1000000 < int(cleaned) < 2000000:
                _cache_price, _cache_info = int(cleaned), "قیمت از متن پیدا شد"
                return _cache_price, _cache_info
        return None, "قیمت پیدا نشد"
    except Exception as e:
        return None, f"خطا: {str(e)}"

# ---------------------
# ساخت ربات و پنل
# ---------------------
bot = Robot(token=BOT_TOKEN)

def admin_panel():
    kb = KeypadBuilder()
    kb.row().button("💵 قیمت دلار", "get_dollar_price")
    kb.row().button("👥 تعداد اعضا", "total_members")
    kb.row().button("🟢 نفرات آنلاین", "online_members")
    return kb

# ---------------------
# مانیتور و گزارش به مدیر
# ---------------------
class Monitor:
    def __init__(self, bot: Robot):
        self.bot = bot
        self.total_messages = 0
        self.total_errors = 0
        self.last_error = None

    def add_message(self):
        self.total_messages += 1

    def add_error(self, error: str):
        self.total_errors += 1
        self.last_error = error

    async def send_report(self):
        text = (
            f"📊 گزارش ربات:\n"
            f"✅ پیام‌ها: {self.total_messages}\n"
            f"⚠️ خطاها: {self.total_errors}\n"
            f"آخرین خطا: {self.last_error or 'ندارد'}"
        )
        try:
            await self.bot.send_message(ADMIN_CHAT, text)
        except Exception as e:
            print("خطا در ارسال گزارش:", e)

    async def auto_report(self, interval=600):
        while True:
            await asyncio.sleep(interval)
            await self.send_report()

monitor = Monitor(bot)

# ---------------------
# مدیریت پیام‌ها
# ---------------------
@bot.on_message()
async def handle(bot: Robot, message: Message):
    text = (message.text or "").strip().lower()
    chat_id = str(message.chat_id)

    add_user(chat_id)
    monitor.add_message()

    try:
        # پنل فقط برای مدیر
        if chat_id == ADMIN_CHAT:
            await message.reply("پنل مدیریت شما فعال است", keyboard=admin_panel())

        # دکمه‌ها
        if message.payload == "get_dollar_price":
            price, info = get_tgju_dollar_price()
            if price:
                await message.reply(
                    f"💵 قیمت دلار آزاد (tgju.org):\n"
                    f"**{price:,} ریال**\n"
                    f"(معادل {price:,} تومان)\n"
                    f"وضعیت: {info}"
                )
            else:
                await message.reply(f"❌ نتونستم قیمت رو بگیرم\nجزئیات: {info}")

        elif message.payload == "total_members":
            total = get_total_members()
            await message.reply(f"👥 تعداد کل اعضا: {total}")

        elif message.payload == "online_members":
            online = get_online_members()
            await message.reply(f"🟢 تعداد نفرات آنلاین: {online}")

        # کاربران عادی
        elif any(word in text for word in ["دلار", "قیمت دلار"]):
            price, info = get_tgju_dollar_price()
            if price:
                await message.reply(
                    f"💵 قیمت دلار آزاد (tgju.org):\n"
                    f"**{price:,} ریال**\n"
                    f"(معادل {price:,} تومان)\n"
                    f"وضعیت: {info}"
                )
            else:
                await message.reply(f"❌ نتونستم قیمت رو بگیرم\nجزئیات: {info}")

        elif any(word in text for word in ["سلام","start","/start","/help"]):
            await message.reply(
                "سلام! ربات قیمت دلار فعاله 😊\n"
                "برای دریافت قیمت دلار دکمه 💵 'قیمت دلار' رو بزن"
            )

        elif text in ["chatid","چت آیدی"]:
            await message.reply(f"chat_id شما: {message.chat_id}")

    except Exception as e:
        monitor.add_error(str(e))
        await message.reply("⚠️ خطایی رخ داد! بعداً دوباره امتحان کن")
        print("خطا:", e)

# ---------------------
# اجرای همزمان ربات و مانیتور
# ---------------------
async def main():
    await asyncio.gather(
        bot.run(),
        monitor.auto_report(interval=600)  # گزارش هر ۱۰ دقیقه
    )

asyncio.run(main())

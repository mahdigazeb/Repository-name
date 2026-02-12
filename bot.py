from rubka.asynco import Robot
from rubka.context import Message
import asyncio
import requests
from bs4 import BeautifulSoup
import re

# توکن ربات رو یا مستقیم بنویس یا از متغیر محیطی بگیر
# برای امنیت بیشتر روی Render پیشنهاد می‌کنم از متغیر محیطی استفاده کنی
BOT_TOKEN = "HCBGJ0KFRPWPWZQJEUMMXZEGQKUAZYIWQIXKPVNANIHGMSVPIJPEFPGKLJEKTPZP"

bot = Robot(token=BOT_TOKEN)

print("ربات شروع شد...")

def get_tgju_dollar_price():
    try:
        url = "https://www.tgju.org/profile/price_dollar_rl"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return None, f"سایت جواب نداد (کد {r.status_code})"

        soup = BeautifulSoup(r.text, "html.parser")

        # روش ۱: جستجو برای تگ‌های رایج قیمت در tgju
        price_tags = soup.find_all(["span", "td", "div"], class_=[
            "info-price", "value", "data-value", "price", "number", "tgju-price", "market-price", "data-field"
        ])
        
        for tag in price_tags:
            text = tag.get_text(strip=True).replace(',', '').replace(' ', '').replace('ریال', '').replace('تومان', '')
            if re.match(r'^\d+$', text) and 1000000 < int(text) < 2000000:
                return int(text), "قیمت از تگ مستقیم پیدا شد"

        # روش ۲: جستجو در متن صفحه
        all_text = soup.get_text(separator=" ", strip=True)
        pos = all_text.find("دلار")
        if pos != -1:
            segment = all_text[max(0, pos-200):pos+400]
            numbers = re.findall(r'\d{1,3}(?:,\d{3})+', segment)
            for num in numbers:
                cleaned = num.replace(',', '')
                if cleaned.isdigit() and 1000000 < int(cleaned) < 2000000:
                    return int(cleaned), "قیمت تقریبی از متن صفحه پیدا شد"

        # روش ۳: جستجوی همه اعداد بزرگ در صفحه
        all_numbers = re.findall(r'\d{1,3}(?:,\d{3})+', all_text)
        for num in all_numbers:
            cleaned = num.replace(',', '')
            if cleaned.isdigit() and 1000000 < int(cleaned) < 2000000:
                return int(cleaned), "قیمت از اعداد صفحه پیدا شد"

        return None, "قیمت پیدا نشد - ممکنه ساختار سایت تغییر کرده باشه"

    except Exception as e:
        return None, f"خطا: {str(e)}"

@bot.on_message()
async def handle(bot: Robot, message: Message):
    text = (message.text or "").strip().lower()

    print(f"پیام دریافتی: '{text}' از chat_id: {message.chat_id}")

    # درخواست قیمت دلار
    if any(word in text for word in ["دلار", "قیمت دلار", "دلار چند", "قیمت", "/dollar", "tgju", "tgju.org"]):
        price, info = get_tgju_dollar_price()
        if price:
            await message.reply(
                f"قیمت دلار آزاد (از tgju.org):\n"
                f"**{price:,} ریال**\n"
                f"(معادل {price:,} تومان)\n"
                f"منبع: https://www.tgju.org/profile/price_dollar_rl\n"
                f"وضعیت: {info}"
            )
        else:
            await message.reply(
                f"متأسفانه نتونستم قیمت رو بگیرم 😔\n"
                f"جزئیات: {info}\n"
                "بعداً دوباره امتحان کن"
            )

    # سلام و تست
    elif any(word in text for word in ["سلام", "تست", "شروع", "start", "hi", "/start", "/help"]):
        await message.reply(
            "سلام! ربات قیمت دلار فعاله 😊\n"
            "بنویس قیمت دلار یا دلار تا قیمت لحظه‌ای از tgju برات بگیرم\n"
            "یا آدرس سایت بده تا متنش رو برات کپی کنم"
        )

    # نمایش chat_id (برای دیباگ)
    elif text == "chatid" or text == "چت آیدی":
        await message.reply(f"chat_id شما: {message.chat_id}")

asyncio.run(bot.run())

import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN is not set!")
    exit()

async def clear_updates():
    bot = Bot(token=TOKEN)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        updates = await bot.get_updates()
        print(f"Cleared {len(updates)} pending updates")
    except TelegramError as e:
        print(f"Telegram API error: {e}")

asyncio.run(clear_updates())

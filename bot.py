import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN is not set!")
    exit()

async def clear_updates():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    updates = await bot.get_updates()
    print(f"Cleared {len(updates)} pending updates")

asyncio.run(clear_updates())

print("✅ Bot token loaded successfully.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /price to get BTC price.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json")
        btc_price = response.json()["bpi"]["USD"]["rate"]
        await update.message.reply_text(f"🟡 BTC price: ${btc_price}")
    except Exception as e:
        await update.message.reply_text("⚠️ Error fetching price.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))

app.run_polling()

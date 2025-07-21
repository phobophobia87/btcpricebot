import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# Load token from environment
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Check if token exists
if not TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN is not set!")
    exit()

print("✅ Bot token loaded successfully.")

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /price to get BTC price.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice/BTC.json")
        btc_price = response.json()["bpi"]["USD"]["rate"]
        await update.message.reply_text(f"🟡 BTC price: ${btc_price}")
    except Exception as e:
        await update.message.reply_text("⚠️ Error fetching price.")

# Build the app
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))

# Run the bot
app.run_polling()

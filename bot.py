import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("7871181641:AAECAlUG47815PoZZnYfXpF5DgHOcNwQ7YE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Send /price to get the current Bitcoin price.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
        response = requests.get(url)
        data = response.json()
        price = data["bpi"]["USD"]["rate"]
        await update.message.reply_text(f"💰 Current Bitcoin Price: ${price}")
    except Exception as e:
        await update.message.reply_text("Error fetching Bitcoin price.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import asyncio
import logging
import requests
import time

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from requests.exceptions import HTTPError

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the Telegram Token from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    logger.error("❌ ERROR: TELEGRAM_TOKEN is not set!")

async def start(update: Update, context):
    """Sends a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can give you cryptocurrency prices and 24h changes. "
        "Try typing /prices."
    )
    logger.info(f"User {user.full_name} ({user.id}) started the bot.")

async def get_crypto_prices(update: Update, context):
    """Sends the current prices and 24h changes for multiple cryptocurrencies when the command /prices is issued."""
    logger.info("Received /prices command. Fetching cryptocurrency prices and 24h changes...")
    
    # Define the cryptocurrencies with their desired output symbol and CoinGecko ID
    cryptos = {
        "btc": "bitcoin",
        "apt": "aptos",
        "cake": "pancakeswap-token",
        "sand": "the-sandbox",
        "imx": "immutable-x",
        "rndr": "render-token" # Added Render Token
    }
    
    # Create a comma-separated string of CoinGecko IDs for the API request
    coin_ids = ",".join(cryptos.values())
    
    max_retries = 5
    initial_wait_time = 2

    for attempt in range(max_retries):
        try:
            # Using CoinGecko API to get prices for multiple coins, including 24hr change
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            price_messages = []
            # Iterate through the cryptos dictionary to get the desired symbol and CoinGecko ID
            for symbol, cg_id in cryptos.items():
                if cg_id in data and "usd" in data[cg_id]:
                    price = data[cg_id]["usd"]
                    formatted_price = f"{price:,.2f}"
                    
                    change_24h = data[cg_id].get("usd_24h_change")
                    
                    change_str = ""
                    if change_24h is not None:
                        change_str = f" ({change_24h:+.2f}%)"
                        
                    # Format the output using the symbol from the dictionary
                    price_messages.append(f"{symbol.upper()}: ${formatted_price}{change_str}")
                else:
                    # If price not available, still show the symbol
                    price_messages.append(f"{symbol.upper()}: Price not available")

            # Join all price messages into one string
            full_message = "Current Cryptocurrency Prices (USD):\n" + "\n".join(price_messages)

            await update.message.reply_text(full_message)
            logger.info(f"Sent cryptocurrency prices:\n{full_message}")
            return # Exit the function after successful retrieval

        except HTTPError as e:
            if e.response.status_code == 429:
                wait_time = initial_wait_time * (2 ** attempt) # Exponential backoff
                logger.warning(f"Rate limit hit (429) on attempt {attempt + 1}. Retrying in {wait_time} seconds...")
                if attempt < max_retries - 1:
                    await update.message.reply_text(f"Whoa, too many requests! Please wait a moment. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time) # Asynchronous sleep
            else:
                logger.error(f"HTTP Error fetching crypto prices from CoinGecko: {e}")
                await update.message.reply_text(f"Sorry, I couldn't retrieve the crypto prices due to an API error ({e.response.status_code}). Please try again later.")
                return
        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error fetching crypto prices from CoinGecko: {e}")
            await update.message.reply_text("Sorry, I couldn't retrieve the crypto prices at the moment

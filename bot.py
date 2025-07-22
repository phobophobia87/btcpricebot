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
        f"Hi {user.mention_html()}! I'm a bot that can give you cryptocurrency prices, 24h changes, and calculate your total holdings. "
        "Try typing /prices."
    )
    logger.info(f"User {user.full_name} ({user.id}) started the bot.")

async def get_crypto_prices(update: Update, context):
    """Sends the current prices and 24h changes for multiple cryptocurrencies and calculates total value."""
    logger.info("Received /prices command. Fetching cryptocurrency prices and 24h changes, and calculating total value...")
    
    # Define the cryptocurrencies with their desired output symbol and CoinGecko ID
    cryptos = {
        "btc": "bitcoin",
        "apt": "aptos",
        "cake": "pancakeswap-token",
        "sand": "the-sandbox",
        "imx": "immutable-x",
        "render": "render-token", 
        "fet": "fetch-ai",    
        "eth": "ethereum"     
    }

    # Define your specific holdings (quantities) for total value calculation
    # IMPORTANT: Update these values to reflect your actual holdings!
    user_holdings = {
        "apt": 4.19,
        "render": 4.88,
        "fet": 51.43,
        "imx": 34.39,
        "sand": 61.13,
        # Add quantities for BTC, CAKE, ETH if you hold them and want them in the total calculation
        # "btc": 0.001,
        # "cake": 10.5,
        # "eth": 0.05,
    }
    
    # Create a comma-separated string of CoinGecko IDs for the API request
    # Ensure all coins in user_holdings are also in cryptos, or their prices won't be fetched
    all_coin_ids_needed = set(cryptos.values())
    
    coin_ids = ",".join(all_coin_ids_needed)
    
    max_retries = 5
    initial_wait_time = 2

    current_prices_fetched = {} # To store fetched prices for total calculation

    for attempt in range(max_retries):
        try:
            # Using CoinGecko API to get prices for multiple coins, including 24hr change
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            price_messages = []
            
            # --- Process prices for display ---
            for symbol, cg_id in cryptos.items():
                if cg_id in data and "usd" in data[cg_id]:
                    price = data[cg_id]["usd"]
                    current_prices_fetched[symbol] = price # Store price for total calculation
                    formatted_price = f"{price:,.2f}"
                    
                    change_24h = data[cg_id].get("usd_24h_change")
                    
                    change_str = ""
                    if change_24h is not None:
                        change_str = f" ({change_24h:+.2f}%)"
                        
                    price_messages.append(f"{symbol.upper()}: ${formatted_price}{change_str}")
                else:
                    price_messages.append(f"{symbol.upper()}: Price not available")

            # --- Calculate total value of holdings ---
            total_holdings_value = 0
            holdings_calculated_count = 0
            for symbol, quantity in user_holdings.items():
                if symbol in current_prices_fetched:
                    total_holdings_value += quantity * current_prices_fetched[symbol]
                    holdings_calculated_count += 1
                else:
                    logger.warning(f"Price for {symbol.upper()} not available for total calculation.")
            
            # --- Construct final message ---
            full_message = "Current Cryptocurrency Prices (USD):\n" + "\n".join(price_messages)
            
            if holdings_calculated_count > 0:
                full_message += f"\n\nTotal Estimated Value of Holdings: ${total_holdings_value:,.2f}"
            else:
                full_message += "\n\nCould not calculate total estimated value (prices unavailable)."


            await update.message.reply_text(full_message)
            logger.info(f"Sent cryptocurrency prices and total value:\n{full_message}")
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
            await update.message.reply_text("Sorry, I couldn't retrieve the crypto prices at the moment due to a network issue. Please try again later.")
            return
        except KeyError as e:
            logger.error(f"Unexpected API response format from CoinGecko: Missing key {e}")
            await update.message.reply_text("Sorry, there was an issue parsing the crypto price data. Please try again later.")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred in get_crypto_prices: {e}", exc_info=True)
            await update.message.reply_text("An unexpected error occurred. Please try again.")
            return

    # If all retries fail
    logger.error(f"Failed to fetch crypto prices after {max_retries} attempts due to persistent issues.")
    await update.message.reply_text("I'm having trouble getting the cryptocurrency prices right now. Please try again in a few minutes.")


async def echo(update: Update, context):
    """Echo the user message. This handler responds to any non-command text."""
    logger.info(f"Received message from {update.effective_user.full_name} ({update.effective_user.id}): {update.message.

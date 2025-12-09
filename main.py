import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to AstraScout Crypto Bot 🚀\n\n"
        "Commands:\n"
        "/price BTC\n"
        "/feargreed"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_URL}/price/{symbol}"

    r = requests.get(url, timeout=10)
    data = r.json()

    await update.message.reply_text(f"{symbol} price:\n{data}")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{INSIGHTS_API_URL}/feargreed"
    r = requests.get(url, timeout=10)
    data = r.json()

    await update.message.reply_text(f"Fear & Greed Index:\n{data}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    print("AstraScout bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

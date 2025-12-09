import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("ASTRASCOUTCRYPTOBOT")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")

# -------- Commands --------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 AstraScout Crypto Bot\n\n"
        "Commands:\n"
        "/price BTC\n"
        "/feargreed\n"
        "/market"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_URL}/price/{symbol}"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        await update.message.reply_text(f"💰 {symbol} price:\n{data}")
    except Exception as e:
        await update.message.reply_text("Error fetching price")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{INSIGHTS_API_URL}/feargreed"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        await update.message.reply_text(f"😱 Fear & Greed Index:\n{data}")
    except:
        await update.message.reply_text("Error fetching Fear & Greed data")

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{INSIGHTS_API_URL}/market/insights"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        await update.message.reply_text(f"📊 Market Insights:\n{data}")
    except:
        await update.message.reply_text("Error fetching market insights")

# -------- Run --------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))
    app.add_handler(CommandHandler("market", market))

    app.run_polling()

if __name__ == "__main__":
    main()

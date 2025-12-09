import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")

if not BOT_TOKEN or not CRYPTO_API_URL or not INSIGHTS_API_URL:
    raise ValueError("Missing environment variables")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "AstraScout Crypto Bot is live.\n\n"
        "Commands:\n"
        "/price BTC\n"
        "/feargreed"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_URL}/{symbol}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        price = data.get("price")
        if price is None:
            raise ValueError("No price in response")

        await update.message.reply_text(f"{symbol}: ${price}")
    except Exception:
        await update.message.reply_text("Could not fetch price")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(INSIGHTS_API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()

        score = data.get("fear_greed_index")
        label = data.get("classification")

        await update.message.reply_text(
            f"Fear & Greed Index\nScore: {score}\nSentiment: {label}"
        )
    except Exception:
        await update.message.reply_text("Could not fetch Fear & Greed")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))
    app.run_polling()

if __name__ == "__main__":
    main()

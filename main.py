import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST")

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("BOT TOKEN ontbreekt")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt")

def rapid_headers(host):
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host
    }

# ---------- Commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "/price BTC\n"
        "/feargreed"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()

    r = requests.get(
        f"{CRYPTO_API_URL}/{symbol}",
        headers=rapid_headers(CRYPTO_API_HOST),
        timeout=10
    )

    data = r.json()
    price = data.get("price_usd")

    await update.message.reply_text(
        f"💰 {symbol}: ${price}\nSource: {data.get('source')}"
    )

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = requests.get(
        INSIGHTS_API_URL,
        headers=rapid_headers(INSIGHTS_API_HOST),
        timeout=10
    )

    data = r.json()

    await update.message.reply_text(
        f"📊 Fear & Greed Index\n"
        f"Score: {data.get('fear_greed_index')}\n"
        f"Sentiment: {data.get('classification')}"
    )

# ---------- Scheduled Job ----------

async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    try:
        price_resp = requests.get(
            f"{CRYPTO_API_URL}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10
        ).json()

        fg_resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10
        ).json()

        message = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC: ${price_resp.get('price_usd')}\n"
            f"😨 Fear & Greed: {fg_resp.get('fear_greed_index')} "
            f"({fg_resp.get('classification')})\n\n"
            "_Powered by AstraScout APIs_"
        )

        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        print("Scheduled job error:", e)

# ---------- Main ----------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    app.job_queue.run_repeating(
        scheduled_update,
        interval=300,
        first=10
    )

    print("✅ Bot running")
    app.run_polling()

if __name__ == "__main__":
    main()

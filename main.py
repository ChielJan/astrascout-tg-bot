import os
import requests

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# --------------------
# Environment variables
# --------------------
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST")

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --------------------
# Safety checks
# --------------------
if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt in Railway variables")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt in Railway variables")

if not CRYPTO_API_URL or not CRYPTO_API_HOST:
    raise ValueError("CRYPTO_API_URL of CRYPTO_API_HOST ontbreekt")

if not INSIGHTS_API_URL or not INSIGHTS_API_HOST:
    raise ValueError("INSIGHTS_API_URL of INSIGHTS_API_HOST ontbreekt")


def rapid_headers(host: str) -> dict:
    """Headers voor RapidAPI calls."""
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


# --------------------
# Commands
# --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Beschikbare commands:\n"
        "/price BTC – huidige prijs\n"
        "/feargreed – Fear & Greed index"
    )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()

    try:
        r = requests.get(
            f"{CRYPTO_API_URL}/{symbol}",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        # Jouw API geeft 'price_usd' terug
        price_usd = data.get("price_usd")
        source = data.get("source", "unknown")

        if price_usd is None:
            raise Exception(f"Geen 'price_usd' veld in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price_usd}\nBron: {source}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon prijs niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        score = data.get("fear_greed_index")
        label = data.get("classification")

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon Fear & Greed niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


# --------------------
# Scheduler voor kanaal updates
# --------------------
async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    """Stuur elke X minuten een update naar je kanaal."""
    try:
        # BTC prijs via Rapid
        price_resp = requests.get(
            f"{CRYPTO_API_URL}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        price_resp.raise_for_status()
        price_data = price_resp.json()
        btc_price = price_data.get("price_usd")
        price_source = price_data.get("source", "unknown")

        # Fear & Greed via Rapid
        fg_resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        fg_resp.raise_for_status()
        fg_data = fg_resp.json()
        fg_score = fg_data.get("fear_greed_index")
        fg_label = fg_data.get("classification")

        message = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC Price: ${btc_price} (bron: {price_source})\n"
            f"😨 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs"
        )

        if TELEGRAM_CHAT_ID:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            print("TELEGRAM_CHAT_ID niet gezet – sla scheduled update over.")

    except Exception as e:
        print("Scheduled job error:", e)


# --------------------
# Main
# --------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    # Job queue voor elke 5 minuten update
    job_queue = app.job_queue
    job_queue.run_repeating(
        scheduled_update,
        interval=300, # 5 minuten
        first=10, # eerste run na 10 seconden
    )

    print("✅ AstraScout bot gestart")
    app.run_polling()


if __name__ == "__main__":
    main()

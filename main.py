import os
import requests

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ====== ENV VARS ======
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # bv astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST") # bv astrascout-market-insights-api.p.rapidapi.com


# ====== CHECKS ======
if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt")

if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID ontbreekt")

# ====== HELPERS ======
def rapid_headers(host: str) -> dict:
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


# ====== COMMAND HANDLERS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Available commands:\n"
        "/price BTC – current price\n"
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


# ====== PERIODIC JOB ======
async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    """
    Stuur elke 5 minuten een update naar TELEGRAM_CHAT_ID.
    """
    try:
        # BTC price via RapidAPI
        r_price = requests.get(
            f"{CRYPTO_API_URL}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        r_price.raise_for_status()
        price_data = r_price.json()
        btc_price = price_data.get("price_usd")
        price_source = price_data.get("source", "unknown")

        # Fear & Greed via RapidAPI
        r_fg = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        r_fg.raise_for_status()
        fg_data = r_fg.json()
        fg_score = fg_data.get("fear_greed_index")
        fg_label = fg_data.get("classification")

        text = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC: ${btc_price} (bron: {price_source})\n"
            f"📈 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs via RapidAPI"
        )

        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        # Dit crasht de bot niet – je ziet het alleen in de Railway logs
        print("Scheduled job error:", e)


# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    # JobQueue: elke 5 minuten runnen, eerste keer na 10 sec
    app.job_queue.run_repeating(
        scheduled_update,
        interval=300,
        first=10,
    )

    print("✅ Bot gestart met JobQueue")
    app.run_polling()


if __name__ == "__main__":
    main()

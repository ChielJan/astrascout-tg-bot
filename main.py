import os
import requests

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# -------------------------------------------------
# ENV VARS
# -------------------------------------------------
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv: https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # bv: astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv: https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST") # bv: astrascout-market-insights-api.p.rapidapi.com

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # van @RawDataBot

# Basic checks
if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt in Railway variables")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt in Railway variables")


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def rapid_headers(host: str) -> dict:
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


def fetch_price(symbol: str) -> dict:
    """Haalt prijs op via RapidAPI (Price API)."""
    url = f"{CRYPTO_API_URL}/{symbol}"
    r = requests.get(url, headers=rapid_headers(CRYPTO_API_HOST), timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_fear_greed() -> dict:
    """Haalt Fear & Greed op via RapidAPI (Insights API)."""
    r = requests.get(INSIGHTS_API_URL,
                     headers=rapid_headers(INSIGHTS_API_HOST),
                     timeout=10)
    r.raise_for_status()
    return r.json()


# -------------------------------------------------
# COMMAND HANDLERS
# -------------------------------------------------
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
        data = fetch_price(symbol)
        price_usd = data.get("price_usd")
        source = data.get("source", "unknown")

        if price_usd is None:
            raise Exception(f"Geen 'price_usd' veld in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price_usd}\n"
            f"Bron: {source}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon prijs niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = fetch_fear_greed()
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


# -------------------------------------------------
# JOBQUEUE: elke 5 min post naar kanaal
# -------------------------------------------------
async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    if not TELEGRAM_CHAT_ID:
        # Geen chat id ingesteld -> dan doen we niks
        print("TELEGRAM_CHAT_ID ontbreekt, sla scheduled update over")
        return

    try:
        # BTC price via Rapid
        price_data = fetch_price("BTC")
        btc_price = price_data.get("price_usd")
        price_source = price_data.get("source", "unknown")

        # Fear & Greed via Rapid
        fg_data = fetch_fear_greed()
        fg_score = fg_data.get("fear_greed_index")
        fg_label = fg_data.get("classification")

        message = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC Price: ${btc_price} (bron: {price_source})\n"
            f"😨 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs via RapidAPI"
        )

        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        print("Scheduled job error:", e)


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    # Elke 5 minuten automatisch update sturen
    job_queue = app.job_queue
    job_queue.run_repeating(
        scheduled_update,
        interval=300, # 5 minuten
        first=10, # eerste keer na 10 sec
        name="market_update",
    )

    print("✅ Bot gestart, wacht op updates...")
    app.run_polling()


if __name__ == "__main__":
    main()

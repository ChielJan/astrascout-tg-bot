import os
import requests

from telegram import Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
)

# ---------- ENV VARS ----------

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv: https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # bv: astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv: https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST") # bv: astrascout-market-insights-api.p.rapidapi.com

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # kanaal / chat id voor de 5-min updates


# ---------- CHECKS ----------

if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt")

if not CRYPTO_API_URL or not CRYPTO_API_HOST:
    raise ValueError("CRYPTO_API_URL of CRYPTO_API_HOST ontbreekt")

if not INSIGHTS_API_URL or not INSIGHTS_API_HOST:
    raise ValueError("INSIGHTS_API_URL of INSIGHTS_API_HOST ontbreekt")


# ---------- HULPFUNCTIES ----------

def rapid_headers(host: str) -> dict:
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


# ---------- COMMANDS ----------

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Commands:\n"
        "/price BTC – huidige prijs\n"
        "/feargreed – Fear & Greed index"
    )


def price(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()

    try:
        resp = requests.get(
            f"{CRYPTO_API_URL.rstrip('/')}/{symbol}",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        price_usd = data.get("price_usd")
        if price_usd is None:
            raise ValueError(f"Geen 'price_usd' in response: {data}")

        source = data.get("source", "unknown")

        update.message.reply_text(
            f"💰 {symbol}: ${price_usd}\nBron: {source}"
        )

    except Exception as e:
        update.message.reply_text(
            f"❌ Kon prijs niet ophalen, probeer later opnieuw.\n(debug: {e})"
        )


def feargreed(update: Update, context: CallbackContext) -> None:
    try:
        resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        score = data.get("fear_greed_index")
        label = data.get("classification")

        update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )

    except Exception as e:
        update.message.reply_text(
            f"❌ Kon Fear & Greed niet ophalen.\n(debug: {e})"
        )


# ---------- JOB QUEUE: 5-MIN UPDATE ----------

def scheduled_update(context: CallbackContext) -> None:
    """Stuur elke 5 minuten een update naar TELEGRAM_CHAT_ID (kanaal of chat)."""
    if not TELEGRAM_CHAT_ID:
        # geen kanaal ingesteld, dan doen we niets
        return

    try:
        # BTC prijs via Rapid
        price_resp = requests.get(
            f"{CRYPTO_API_URL.rstrip('/')}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        price_resp.raise_for_status()
        price_data = price_resp.json()
        btc_price = price_data.get("price_usd")

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

        text = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC Price: ${btc_price}\n"
            f"😨 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs"
        )

        context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        print("Scheduled job error:", e)


# ---------- MAIN ----------

def main() -> None:
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("price", price))
    dp.add_handler(CommandHandler("feargreed", feargreed))

    # Elke 5 minuten automatische update (alleen als TELEGRAM_CHAT_ID gezet is)
    if TELEGRAM_CHAT_ID:
        jq = updater.job_queue
        jq.run_repeating(scheduled_update, interval=300, first=10)

    # Bot starten
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

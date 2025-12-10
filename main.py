import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# --- ENV VARS ---

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST")

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # voor de 5-minuten updates

if not BOT_TOKEN:
    raise ValueError("BOT TOKEN ontbreekt")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt")


def rapid_headers(host: str) -> dict:
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Commands:\n"
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

        # jouw API geeft 'price_usd' terug
        price_usd = data.get("price_usd")

        if price_usd is None:
            raise Exception(f"Geen price_usd veld in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price_usd}\n"
            f"Bron: {data.get('source', 'unknown')}"
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

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {data.get('fear_greed_index')}\n"
            f"Sentiment: {data.get('classification')}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon Fear & Greed niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


# --- SCHEDULED JOB (elke 5 minuten) ---

async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    try:
        # Price via RapidAPI
        price_resp = requests.get(
            f"{CRYPTO_API_URL}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        price_resp.raise_for_status()
        price_data = price_resp.json()
        btc_price = price_data.get("price_usd")

        # Fear & Greed via RapidAPI
        fg_resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        fg_resp.raise_for_status()
        fg_data = fg_resp.json()
        fg_score = fg_data.get("fear_greed_index")
        fg_label = fg_data.get("classification")

        if not TELEGRAM_CHAT_ID:
            print("⚠️ TELEGRAM_CHAT_ID niet gezet, scheduled_update wordt overgeslagen")
            return

        message = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC Price: ${btc_price}\n"
            f"😨 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs (via RapidAPI)"
        )

        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        print("Scheduled job error:", e)


# --- MAIN ---

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 5-minuten job
    job_queue = app.job_queue
    job_queue.run_repeating(
        scheduled_update,
        interval=300, # 5 minuten
        first=10, # start na 10 seconden
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    print("✅ AstraScout bot gestart")
    app.run_polling()


if __name__ == "__main__":
    main()

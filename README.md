## AstraScout Telegram Bot

Simple async Telegram bot that fetches:

- Live crypto prices (26 supported coins)  
- The Bitcoin Fear & Greed Index  

using the public **AstraScout** APIs on RapidAPI.

---

## Features

- `/start` – Show bot info and available commands
- `/price <symbol>` – Get the current USD price for a coin  
  - Example: `/price BTC`, `/price ETH`, `/price SOL`
- `/feargreed` – Get the latest Fear & Greed score and sentiment

Under the hood the bot calls:

- **Crypto Price API** – `CRYPTO_API_URL` / `CRYPTO_API_HOST`
- **Market Insights API** – `INSIGHTS_API_URL` / `INSIGHTS_API_HOST`

---

## Requirements

- Python 3.10+
- `python-telegram-bot` (async, v20+)
- `requests`

Install dependencies (example):

```bash
pip install -r requirements.txt


---

Environment Variables

The bot is configured entirely via environment variables:

ASTRASCOUT_BOT_TOKEN # Telegram bot token from @BotFather
RAPID_API_KEY # Your RapidAPI key

TELEGRAM_CHAT_ID # Chat or channel ID where the bot may post

CRYPTO_API_URL # e.g. https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST # e.g. astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL # e.g. https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST # e.g. astrascout-market-insights-api.p.rapidapi.com

> Note:
TELEGRAM_CHAT_ID should be the ID of the chat or channel where the bot is allowed to send messages. For channels the bot must be added as an admin with permission to post messages.




---

How It Works

/price <symbol>

When a user sends:

/price BTC

the bot does:

r = requests.get(
    f"{CRYPTO_API_URL}/BTC",
    headers={
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": CRYPTO_API_HOST,
    },
    timeout=10,
)
data = r.json()
# -> expects fields like: {"price_usd": 43000, "source": "binance"}

and replies with:

💰 BTC: $43000
Bron: binance

Any supported symbol (26 coins) can be requested in the same way.

/feargreed

For:

/feargreed

the bot calls the Market Insights API:

r = requests.get(
    INSIGHTS_API_URL,
    headers={
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": INSIGHTS_API_HOST,
    },
    timeout=10,
)
data = r.json()
# -> expects fields like: {"fear_greed_index": 63, "classification": "Greed"}

and replies with:

📊 Fear & Greed Index
Score: 63
Sentiment: Greed


---

Running the Bot

export ASTRASCOUT_BOT_TOKEN="YOUR_BOT_TOKEN"
export RAPID_API_KEY="YOUR_RAPID_KEY"
export TELEGRAM_CHAT_ID="YOUR_CHAT_OR_CHANNEL_ID"
export CRYPTO_API_URL="https://astrascout-crypto-api.p.rapidapi.com/price"
export CRYPTO_API_HOST="astrascout-crypto-api.p.rapidapi.com"
export INSIGHTS_API_URL="https://astrascout-market-insights-api.p.rapidapi.com/feargreed"
export INSIGHTS_API_HOST="astrascout-market-insights-api.p.rapidapi.com"

python main.py

You should see:

✅ Bot gestart met JobQueue

and the bot will start responding to /start, /price and /feargreed in Telegram.


---

Notes

Errors from the APIs are caught and shown as a simple error message to the user,
while the full exception is printed to the logs (e.g. on Railway).

The bot is intentionally lightweight and focused on just prices and sentiment, powered entirely by the two AstraScout APIs.

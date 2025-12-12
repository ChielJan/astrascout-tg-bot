AstraScout Telegram Bot

A simple Telegram bot that delivers real-time crypto prices (26 supported assets) and market sentiment (Fear & Greed Index) — powered by the AstraScout APIs.

Perfect for traders, analysts, bots, dashboards or anyone who wants fast market data directly inside Telegram.


---

🚀 Features

📈 Crypto Price API

Fetch live prices for 26 cryptocurrencies, including:

BTC, ETH, SOL, XRP

AVAX, ADA, DOGE, SHIB

And many others


Uses multi-source logic for better uptime and fewer null values.

😨 Fear & Greed Index

Returns:

Current F&G score

Classification (Fear, Neutral, Greed)

Updated daily


Great for simple sentiment bots and dashboards.


---

🧰 Commands

Command Description

/price BTC Get the latest price for any supported asset
/feargreed Returns the latest market sentiment



---

🔌 APIs Used

1️⃣ Crypto Price API

RapidAPI:
https://rapidapi.com/AstraScout/api/astrascout-crypto-api

Endpoints used by the bot:

GET /price/{symbol}

26 supported assets




---

2️⃣ Market Insights (Fear & Greed) API

RapidAPI:
https://rapidapi.com/AstraScout/api/astrascout-market-insights-api

Endpoint used by the bot:

GET /feargreed




---

🛠️ Tech Stack

Python

python-telegram-bot

FastAPI (API backend)

httpx (API calls)



---

📦 Basic Example (How the bot fetches data)

Crypto Price

import requests

r = requests.get(
    "https://astrascout-crypto-api.p.rapidapi.com/price/BTC",
    headers={"X-RapidAPI-Key": "YOUR_KEY"}
).json()

print(r)

Fear & Greed Index

import requests

r = requests.get(
    "https://astrascout-market-insights-api.p.rapidapi.com/feargreed",
    headers={"X-RapidAPI-Key": "YOUR_KEY"}
).json()

print(r)


---

⚙️ Environment Variables Required

Create a .env file with:

ASTRASCOUT_BOT_TOKEN=your_bot_token
CRYPTO_API_URL=https://astrascout-crypto-api.p.rapidapi.com
INSIGHTS_API_URL=https://astrascout-market-insights-api.p.rapidapi.com
RAPID_API_KEY=your_rapidapi_key
TELEGRAM_CHAT_ID=your_channel_or_chat_id


---

🤝 Credits

Built by AstraScout, combining Web3 curiosity with simple, developer-friendly tools.


---

📜 License

MIT License.

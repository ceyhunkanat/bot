import aiohttp
import asyncio

TELEGRAM_BOT_TOKEN = "7743011677:AAH1zVUenghUdSKOI-y9UbL6qVCf1butNqA"
TELEGRAM_CHAT_ID = "1678024978"

async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"Telegram gönderim hatası: {response.status}")
    except Exception as e:
        print(f"Telegram gönderimi sırasında hata oluştu: {e}")

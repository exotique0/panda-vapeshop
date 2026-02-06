import os
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


async def notify_user(telegram_id: str, text: str):
    if not BOT_TOKEN or not telegram_id:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            TG_API_URL,
            json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": "Markdown",
            },
        )


async def notify_user(telegram_id: str, text: str):
    print("🔔 notify_user called", telegram_id, text)

    if not BOT_TOKEN or not telegram_id:
        print("❌ BOT_TOKEN or telegram_id missing")
        return

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            TG_API_URL,
            json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": "Markdown",
            },
        )
        print("📨 Telegram response:", r.status_code, r.text)



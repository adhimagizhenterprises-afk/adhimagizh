"""FCM push notifications (stub — no-ops when credentials are absent)."""
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class PushService:
    async def send(self, device_token: str, title: str, body: str) -> bool:
        if not settings.FCM_SERVER_KEY:
            logger.info(f"[Push stub] Token: {device_token} | Title: {title} | Body: {body}")
            return True
        try:
            import aiohttp
            payload = {
                "to": device_token,
                "notification": {"title": title, "body": body},
            }
            headers = {
                "Authorization": f"key={settings.FCM_SERVER_KEY}",
                "Content-Type": "application/json",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json=payload,
                    headers=headers,
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Push sent to {device_token}")
                        return True
                    logger.warning(f"FCM returned {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Push send failed: {e}")
            return False

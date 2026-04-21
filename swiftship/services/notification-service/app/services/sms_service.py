"""SMS dispatch via Twilio (stub — no-ops when credentials are absent)."""
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self._client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except ImportError:
                logger.warning("twilio package not installed — SMS will be logged only")

    async def send(self, to: str, body: str) -> bool:
        if not self._client:
            logger.info(f"[SMS stub] To: {to} | Body: {body}")
            return True
        try:
            self._client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to,
            )
            logger.info(f"SMS sent to {to}")
            return True
        except Exception as e:
            logger.error(f"SMS send failed to {to}: {e}")
            return False

"""Email dispatch via SMTP (stub — no-ops when credentials are absent)."""
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    async def send(self, to: str, subject: str, body: str) -> bool:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.info(f"[Email stub] To: {to} | Subject: {subject}")
            return True
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USER
            msg["To"] = to

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_sync, msg, to)
            return True
        except Exception as e:
            logger.error(f"Email send failed to {to}: {e}")
            return False

    def _send_sync(self, msg: MIMEText, to: str):
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to, msg.as_string())
        logger.info(f"Email sent to {to}")

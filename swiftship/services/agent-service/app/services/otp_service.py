import random
import logging

logger = logging.getLogger(__name__)


class OTPService:
    """Generates and sends OTP to receiver for delivery verification."""

    async def generate_and_send(self, phone: str, awb_number: str) -> str:
        otp = str(random.randint(100000, 999999))
        logger.info(f"OTP for {awb_number} → {phone}: {otp}")
        # In production: send via Twilio/SMS gateway
        return otp

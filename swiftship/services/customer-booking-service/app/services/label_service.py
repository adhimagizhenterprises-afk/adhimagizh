"""
Label generation service — produces shipping label PDFs.
Stub implementation: sets a placeholder URL. In production this would
render a PDF via reportlab/WeasyPrint and upload it to MinIO/S3.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment

logger = logging.getLogger(__name__)


class LabelService:
    async def generate(self, shipment: Shipment, db: AsyncSession) -> str:
        """
        Generate a shipping label for the given shipment.
        Returns the URL where the label PDF can be accessed.
        """
        # Stub: in production, render PDF and upload to object storage
        label_url = f"/labels/{shipment.awb_number}.pdf"
        shipment.label_url = label_url
        shipment.label_generated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"Label generated for AWB {shipment.awb_number}: {label_url}")
        return label_url

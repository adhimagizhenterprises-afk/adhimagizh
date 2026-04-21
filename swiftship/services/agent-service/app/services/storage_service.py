import logging
from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO-backed object storage for POD photos."""

    async def upload_pod_photo(self, awb_number: str, file: UploadFile, photo_type: str) -> str:
        try:
            from minio import Minio
            import io

            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            bucket = settings.MINIO_BUCKET_POD
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)

            content = await file.read()
            object_name = f"{awb_number}/{photo_type}/{file.filename}"
            client.put_object(
                bucket, object_name, io.BytesIO(content), len(content),
                content_type=file.content_type or "image/jpeg",
            )
            return f"/{bucket}/{object_name}"
        except Exception as e:
            logger.error(f"Failed to upload POD photo: {e}")
            return ""

"""
Configuration — Customer Booking Service
Loaded from environment variables / .env file
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "customer-booking-service"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/booking_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_BOOKING_CREATED: str = "booking.created"
    KAFKA_TOPIC_PICKUP_SCHEDULED: str = "pickup.scheduled"

    # Auth service (for token validation)
    AUTH_SERVICE_URL: str = "http://user-auth-service:8007"

    # MinIO (object storage for labels)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_LABELS: str = "shipping-labels"
    MINIO_BUCKET_POD: str = "proof-of-delivery"

    # Pricing
    BASE_RATE_PER_KG: float = 35.0       # ₹35/kg base
    FUEL_SURCHARGE_PCT: float = 18.0     # 18% fuel surcharge
    GST_PCT: float = 18.0                # 18% GST
    DOCKET_CHARGE: float = 25.0          # Flat docket charge
    COD_CHARGE_PCT: float = 1.5          # 1.5% COD handling

    # Service type multipliers
    SERVICE_MULTIPLIERS: dict = {
        "EXPRESS": 2.5,
        "PRIORITY": 1.8,
        "STANDARD": 1.0,
        "ECONOMY": 0.75,
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

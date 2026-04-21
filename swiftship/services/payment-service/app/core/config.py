from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "payment-service"
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/payment_db"
    REDIS_URL: str = "redis://localhost:6379/5"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    JWT_SECRET: str = "change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "notification-service"
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/notification_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FCM_SERVER_KEY: str = ""
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

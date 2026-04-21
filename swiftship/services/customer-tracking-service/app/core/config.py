from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "customer-tracking-service"
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/tracking_db"
    REDIS_URL: str = "redis://localhost:6379/2"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    AUTH_SERVICE_URL: str = "http://user-auth-service:8007"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

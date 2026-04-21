from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "operations-service"
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/operations_db"
    REDIS_URL: str = "redis://localhost:6379/3"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    AUTH_SERVICE_URL: str = "http://user-auth-service:8007"
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

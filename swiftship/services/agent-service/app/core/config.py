from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "agent-service"
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/agent_db"
    REDIS_URL: str = "redis://localhost:6379/4"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    AUTH_SERVICE_URL: str = "http://user-auth-service:8007"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_POD: str = "proof-of-delivery"
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

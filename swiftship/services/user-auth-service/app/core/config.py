from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "user-auth-service"
    DATABASE_URL: str = "postgresql+asyncpg://swiftship:swiftship_secret@localhost/auth_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change_this_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

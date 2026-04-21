from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://rpg:rpg@localhost:5432/rpgsummary"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    UPLOAD_DIR: str = "./data/uploads"
    MAX_AUDIO_SIZE_MB: int = 2048

    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cuda"
    WHISPER_COMPUTE_TYPE: str = "float16"
    WHISPER_LANGUAGE: str = "pt"

    LLM_API_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.3

    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

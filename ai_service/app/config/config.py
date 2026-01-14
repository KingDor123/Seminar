import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from .env import load_env
class Settings(BaseSettings):
    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")
    # HeBERT Settings
    HEBERT_MODEL_NAME: str = os.getenv("HEBERT_MODEL_NAME")
    # Stanza Settings
    STANZA_LANG: str = os.getenv("STANZA_LANG")
    # Service Settings
    API_PORT: int = os.getenv("API_PORT")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = os.getenv("DB_PORT")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True
    )

settings = Settings()

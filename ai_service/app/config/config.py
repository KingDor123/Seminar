import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # LLM Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")

    # HeBERT Settings
    HEBERT_MODEL_NAME: str = os.getenv("HEBERT_MODEL_NAME")

    # Stanza Settings
    STANZA_LANG: str = os.getenv("STANZA_LANG")

    # Service Settings
    API_PORT: int = int(os.getenv("AI_PORT"))

    # Database Settings - These MUST be provided in .env
    DB_USER: str = Field(..., description="Database user")
    DB_PASSWORD: str = Field(..., description="Database password")
    DB_NAME: str = Field(..., description="Database name")
    DB_HOST: str = os.getenv("DB_HOST", "db")
    DB_PORT: int = os.getenv("DB_PORT")


    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()

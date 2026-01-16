"""
Configuration settings for the Quantum-Ai-PCB-Builder backend.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # RabbitMQ Settings
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    # LLM Settings
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"

    # EDA Tool Settings
    EDA_TOOL_PATH: str = "/usr/local/bin/eda"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

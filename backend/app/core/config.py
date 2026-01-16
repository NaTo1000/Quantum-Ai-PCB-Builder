"""Configuration settings for the application."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Quantum AI PCB Builder"
    debug: bool = False

    # RabbitMQ settings
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "guest")

    # AI service settings
    ai_model_endpoint: str = os.getenv("AI_MODEL_ENDPOINT", "http://localhost:8001")

    class Config:
        env_file = ".env"


settings = Settings()

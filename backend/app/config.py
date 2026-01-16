"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # RabbitMQ Configuration
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "pcbuser"
    rabbitmq_pass: str = "pcbpass"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    
    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Design Storage
    designs_dir: str = "/app/designs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

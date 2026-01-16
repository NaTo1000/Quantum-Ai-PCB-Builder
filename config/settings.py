"""Application settings and configuration.

This module provides centralized configuration management
with support for environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMSettings:
    """LLM configuration settings."""

    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7

    def __post_init__(self):
        """Load settings from environment."""
        self.provider = os.getenv("LLM_PROVIDER", self.provider)
        self.model = os.getenv("LLM_MODEL", self.model)
        self.api_key = os.getenv("LLM_API_KEY", self.api_key)


@dataclass
class SimulationSettings:
    """Simulation configuration settings."""

    spice_backend: str = "ngspice"
    timing_backend: str = "opensta"
    default_process_corner: str = "typical"
    default_temperature: float = 27.0


@dataclass
class QueueSettings:
    """Message queue configuration settings."""

    broker_url: str = "amqp://localhost:5672"
    result_backend: str = "redis://localhost:6379"
    task_timeout: int = 3600

    def __post_init__(self):
        """Load settings from environment."""
        self.broker_url = os.getenv("RABBITMQ_URL", self.broker_url)
        self.result_backend = os.getenv("REDIS_URL", self.result_backend)


@dataclass
class APISettings:
    """API server configuration settings."""

    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    def __post_init__(self):
        """Load settings from environment."""
        self.host = os.getenv("API_HOST", self.host)
        self.port = int(os.getenv("API_PORT", str(self.port)))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"


@dataclass
class Settings:
    """Main application settings."""

    app_name: str = "Quantum-Ai-PCB-Builder"
    version: str = "0.1.0"
    environment: str = "development"

    llm: LLMSettings = field(default_factory=LLMSettings)
    simulation: SimulationSettings = field(default_factory=SimulationSettings)
    queue: QueueSettings = field(default_factory=QueueSettings)
    api: APISettings = field(default_factory=APISettings)

    def __post_init__(self):
        """Load settings from environment."""
        self.environment = os.getenv("ENVIRONMENT", self.environment)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

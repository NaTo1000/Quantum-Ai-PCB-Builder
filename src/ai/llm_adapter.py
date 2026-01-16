"""Pluggable LLM interface for swappable AI backends.

This module provides an abstract interface for LLM integration,
allowing users to swap between OpenAI, Claude, or local LLMs.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Response from an LLM query."""

    content: str
    model: str
    tokens_used: int
    confidence: float = 0.0


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters.

    Implement this interface to add support for new LLM providers.
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt for the LLM.
            max_tokens: Maximum number of tokens in the response.

        Returns:
            LLMResponse containing the generated content.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the underlying model."""
        pass


class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT adapter implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize the OpenAI adapter.

        Args:
            api_key: OpenAI API key. If None, reads from environment.
            model: Model identifier to use.
        """
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a response using OpenAI API.

        Note: This is a stub implementation. Real implementation would
        call the OpenAI API.
        """
        # Stub implementation
        return LLMResponse(
            content="[Stub] OpenAI response for hardware design",
            model=self.model,
            tokens_used=0,
            confidence=0.0,
        )

    def get_model_name(self) -> str:
        """Return the OpenAI model name."""
        return self.model


class ClaudeAdapter(LLMAdapter):
    """Anthropic Claude adapter implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus"):
        """Initialize the Claude adapter.

        Args:
            api_key: Anthropic API key. If None, reads from environment.
            model: Model identifier to use.
        """
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a response using Claude API.

        Note: This is a stub implementation. Real implementation would
        call the Anthropic API.
        """
        # Stub implementation
        return LLMResponse(
            content="[Stub] Claude response for hardware design",
            model=self.model,
            tokens_used=0,
            confidence=0.0,
        )

    def get_model_name(self) -> str:
        """Return the Claude model name."""
        return self.model


class LocalLLMAdapter(LLMAdapter):
    """Local LLM adapter for self-hosted models."""

    def __init__(self, model_path: str, model_name: str = "local-llm"):
        """Initialize the local LLM adapter.

        Args:
            model_path: Path to the local model files.
            model_name: Name identifier for the model.
        """
        self.model_path = model_path
        self.model_name = model_name

    def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        """Generate a response using a local LLM.

        Note: This is a stub implementation. Real implementation would
        load and run a local model.
        """
        # Stub implementation
        return LLMResponse(
            content="[Stub] Local LLM response for hardware design",
            model=self.model_name,
            tokens_used=0,
            confidence=0.0,
        )

    def get_model_name(self) -> str:
        """Return the local model name."""
        return self.model_name

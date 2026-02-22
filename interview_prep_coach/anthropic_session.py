"""Anthropic Claude session for AI-powered features."""

import os
from dataclasses import dataclass, field
from typing import Any, Optional

import anthropic


@dataclass
class SessionOptions:
    """Options for Claude session."""

    system_prompt: str = "You are a helpful assistant."
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    retry_attempts: int = 2


@dataclass
class SessionResponse:
    """Response from Claude session."""

    content: str
    error: Optional[str] = None
    usage: dict = field(default_factory=dict)


class ClaudeSession:
    """Async session wrapper for Anthropic Claude API."""

    def __init__(self, options: Optional[SessionOptions] = None):
        """Initialize Claude session.

        Args:
            options: Session options
        """
        self.options = options or SessionOptions()
        self._client: Optional[anthropic.Anthropic] = None
        self._messages: list[dict] = []

    def _get_client(self) -> anthropic.Anthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    async def query(self, prompt: str) -> SessionResponse:
        """Send a query to Claude.

        Args:
            prompt: The prompt to send

        Returns:
            SessionResponse with content or error
        """
        try:
            client = self._get_client()

            # Add user message to history
            self._messages.append({"role": "user", "content": prompt})

            response = client.messages.create(
                model=self.options.model,
                max_tokens=self.options.max_tokens,
                system=self.options.system_prompt,
                messages=self._messages,
                temperature=self.options.temperature,
            )

            content = response.content[0].text if response.content else ""

            # Add assistant response to history
            self._messages.append({"role": "assistant", "content": content})

            return SessionResponse(
                content=content,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )

        except Exception as e:
            return SessionResponse(content="", error=str(e))

    async def __aenter__(self) -> "ClaudeSession":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        pass

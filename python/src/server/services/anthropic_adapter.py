"""
Anthropic Adapter for OpenAI-compatible interface
Converts between OpenAI format and Anthropic format
"""

from anthropic import AsyncAnthropic
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AnthropicAdapter:
    """Adapter to make Anthropic API compatible with OpenAI format"""

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        logger.info("Anthropic adapter initialized")

    async def create_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 4000,
        **kwargs
    ) -> Any:
        """
        Convert OpenAI format request to Anthropic format

        OpenAI format:
        messages = [
            {"role": "system", "content": "You are..."},
            {"role": "user", "content": "Hello"}
        ]

        Anthropic format:
        system = "You are..."
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        """

        # Extract system message
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        # Ensure we have at least one user message
        if not anthropic_messages:
            raise ValueError("At least one non-system message is required")

        # Log the request
        logger.info(
            f"Calling Anthropic API | model={model} | messages={len(anthropic_messages)} | "
            f"system={'yes' if system_message else 'no'} | temp={temperature} | max_tokens={max_tokens}"
        )

        try:
            # Call Anthropic API
            response = await self.client.messages.create(
                model=model, system=system_message, messages=anthropic_messages, temperature=temperature, max_tokens=max_tokens
            )

            # Convert response to OpenAI format
            return self._convert_response(response)

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    def _convert_response(self, anthropic_response):
        """Convert Anthropic response to OpenAI format"""

        # Anthropic response structure
        content = anthropic_response.content[0].text

        # Log token usage
        logger.info(
            f"Anthropic response received | "
            f"input_tokens={anthropic_response.usage.input_tokens} | "
            f"output_tokens={anthropic_response.usage.output_tokens}"
        )

        # OpenAI-compatible format
        class Choice:
            def __init__(self, content):
                self.message = type("Message", (), {"content": content, "role": "assistant"})()
                self.finish_reason = "stop"

        class Response:
            def __init__(self, content, usage):
                self.choices = [Choice(content)]
                self.usage = {
                    "prompt_tokens": usage.input_tokens,
                    "completion_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens,
                }

        return Response(content, anthropic_response.usage)

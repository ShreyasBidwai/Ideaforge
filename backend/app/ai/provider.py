import abc
import asyncio
import logging
from typing import Any, Dict, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProvider(abc.ABC):

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate response from the AI provider."""
        pass


class GeminiProvider(AIProvider):
    model_name: str = "gemini-2.5-flash"

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Configure the genai SDK with the provided API key
        genai.configure(api_key=self.api_key)


    async def generate(
        self,
        prompt: str,
        system_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if response_schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        generation_config = GenerationConfig(**config_kwargs)

        retries = 1
        backoff_delay = 2.0
        attempt = 0
        last_exception = None

        while True:
            try:
                # Initialize model with system instruction
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=system_prompt,
                )

                # Request async content generation
                response = await model.generate_content_async(
                    contents=prompt,
                    generation_config=generation_config,
                )

                if not response.text:
                    raise ValueError(
                        "Gemini response has no text content (possibly blocked or empty)."
                    )
                return response.text

            except Exception as e:
                last_exception = e
                if attempt >= retries:
                    logger.error(
                        f"GeminiProvider failed to generate response after {attempt} retries: {str(e)}"
                    )
                    break

                attempt += 1
                sleep_time = backoff_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"Gemini generation call failed: {str(e)}. "
                    f"Retrying in {sleep_time}s (attempt {attempt}/{retries})..."
                )
                await asyncio.sleep(sleep_time)

        raise last_exception or RuntimeError(
            "GeminiProvider failed to generate response."
        )


def get_ai_provider() -> AIProvider:
    """Factory function to instantiate and return the GeminiProvider."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in Settings.")
    return GeminiProvider(api_key=settings.GEMINI_API_KEY)

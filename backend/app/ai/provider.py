import abc
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.core.config import settings

logger = logging.getLogger(__name__)

FREE_TIER_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",  
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]

class ModelRotator:
    def __init__(self, models: list[str]):
        self.models = models
        self.current_index = 0
        self.exhausted: dict[str, datetime] = {}  # model -> when it was exhausted
    
    def get_current_model(self) -> str:
        """Get next available model, skipping exhausted ones"""
        self._reset_expired()
        for i in range(len(self.models)):
            idx = (self.current_index + i) % len(self.models)
            model = self.models[idx]
            if model not in self.exhausted:
                self.current_index = idx
                return model
        raise Exception("All free-tier Gemini models exhausted for today.")
    
    def mark_exhausted(self, model: str):
        """Mark a model as quota-exhausted"""
        self.exhausted[model] = datetime.utcnow()
        self.current_index = (self.models.index(model) + 1) % len(self.models)
    
    def _reset_expired(self):
        """Reset models exhausted more than 24 hours ago"""
        now = datetime.utcnow()
        self.exhausted = {m: t for m, t in self.exhausted.items() if (now - t).total_seconds() < 86400}
    
    def get_status(self) -> dict:
        """Return status of all models"""
        return {m: ("exhausted" if m in self.exhausted else "available") for m in self.models}

model_rotator = ModelRotator(FREE_TIER_MODELS)


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

        tried_models = set()
        while True:
            try:
                current_model = model_rotator.get_current_model()
            except Exception as e:
                logger.error(f"All free-tier Gemini models exhausted. Consider upgrading to paid API. Error: {e}")
                raise RuntimeError("All free-tier Gemini models exhausted. Consider upgrading to paid API.") from e

            if len(tried_models) >= len(model_rotator.models):
                logger.error("All free-tier Gemini models exhausted. Consider upgrading to paid API.")
                raise RuntimeError("All free-tier Gemini models exhausted. Consider upgrading to paid API.")

            tried_models.add(current_model)

            try:
                # Initialize model with system instruction
                model = genai.GenerativeModel(
                    model_name=current_model,
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
                
                if response_schema is not None:
                    try:
                        import json
                        import re
                        cleaned = response.text.strip()
                        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
                        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
                        cleaned = cleaned.strip()
                        
                        def escape_raw_control_chars(s: str) -> str:
                            result = []
                            in_string = False
                            escaped = False
                            for char in s:
                                if char == '"' and not escaped:
                                    in_string = not in_string
                                    result.append(char)
                                elif char == '\\' and in_string:
                                    escaped = not escaped
                                    result.append(char)
                                else:
                                    if in_string:
                                        if char == '\n':
                                            result.append('\\n')
                                        elif char == '\r':
                                            result.append('\\r')
                                        elif char == '\t':
                                            result.append('\\t')
                                        else:
                                            result.append(char)
                                    else:
                                        result.append(char)
                                    escaped = False
                            return "".join(result)
                        
                        json.loads(escape_raw_control_chars(cleaned))
                    except Exception as json_err:
                        raise ValueError(f"Model returned invalid/truncated JSON: {json_err}")

                return response.text

            except Exception as e:
                err_msg = str(e).lower()
                is_quota_error = "quota" in err_msg or "429" in err_msg or "resourceexhausted" in err_msg
                is_invalid_json = "invalid/truncated json" in err_msg

                if is_quota_error or is_invalid_json:
                    logger.warning(f"Model {current_model} failed (quota or malformed JSON: {str(e)}), rotating to next model")
                    model_rotator.mark_exhausted(current_model)
                    # Retry immediately with the next model
                    continue
                else:
                    # Non-quota error, raise immediately
                    logger.error(f"GeminiProvider failed with non-quota error using model {current_model}: {str(e)}")
                    raise e


def get_ai_provider() -> AIProvider:
    """Factory function to instantiate and return the GeminiProvider."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in Settings.")
    return GeminiProvider(api_key=settings.GEMINI_API_KEY)

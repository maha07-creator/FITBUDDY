"""
Shared helper for calling Gemini with a structured JSON schema.
"""
from __future__ import annotations

import logging
import time
from typing import TypeVar

from pydantic import BaseModel

from .config import settings

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

MAIN_MODEL_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 2


class AIGenerationError(RuntimeError):
    """Raised when Gemini does not return a usable response."""


def generate_structured(
    *,
    model: str,
    system: str,
    prompt: str,
    schema: type[T],
    temperature: float,
    max_output_tokens: int,
) -> T:
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        # Gemini "thinking" tokens count against max_output_tokens
        # and can truncate the JSON. Disable thinking for these calls.
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

    # Busy models (503) and rate limits (429) are usually temporary:
    # retry the main model, then try the fallback model once.
    attempts = [model] * MAIN_MODEL_ATTEMPTS
    fallback = settings.gemini_fallback_model
    if fallback and fallback != model:
        attempts.append(fallback)

    for i, attempt_model in enumerate(attempts):
        try:
            response = client.models.generate_content(
                model=attempt_model, contents=prompt, config=config
            )
            break
        except errors.APIError as exc:
            busy = isinstance(exc, errors.ServerError) or exc.code == 429
            if busy and i < len(attempts) - 1:
                logger.warning(
                    "Gemini model %s busy (%s), retrying", attempt_model, exc.code
                )
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            if busy:
                raise AIGenerationError(
                    "The AI service is busy right now. Please try again in a moment."
                ) from exc
            raise AIGenerationError(
                f"The AI service rejected the request ({exc.code}): {exc.message}"
            ) from exc

    text = response.text
    if not text:
        raise AIGenerationError(
            "The AI returned an empty response. Please try again."
        )

    try:
        return schema.model_validate_json(text)
    except Exception as exc:
        raise AIGenerationError(
            "The AI returned an incomplete plan. Please try again."
        ) from exc

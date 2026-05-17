"""
LLM Service — thin wrapper around the Anthropic SDK.

Why an abstraction layer?
  • Swap models without touching agent code
  • Add retry logic, caching, and cost tracking in one place
  • Mock easily in tests (just patch get_llm_response)
"""

import logging
import time

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

# Initialise client once — reuse across requests (thread-safe)
_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def get_llm_response(
    prompt: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """
    Send a single-turn prompt to the configured LLM and return the text response.

    Args:
        prompt:      The user-turn message.
        model:       Override the default model from config.
        max_tokens:  Override the default max_tokens.
        temperature: Override the default temperature.

    Returns:
        The model's text output as a plain string.

    Raises:
        anthropic.APIError on unrecoverable failures (after retries).
    """
    _model       = model       or settings.llm_model
    _max_tokens  = max_tokens  or settings.llm_max_tokens
    _temperature = temperature or settings.llm_temperature

    for attempt in range(1, settings.max_retries + 2):  # +2 = initial + retries
        try:
            start    = time.perf_counter()
            response = _client.messages.create(
                model      = _model,
                max_tokens = _max_tokens,
                temperature= _temperature,
                messages   = [{"role": "user", "content": prompt}],
            )
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            text    = response.content[0].text
            logger.debug(f"LLM call OK ({elapsed} ms, {response.usage.output_tokens} tok)")
            return text

        except anthropic.RateLimitError:
            wait = 2 ** attempt
            logger.warning(f"Rate-limited. Retrying in {wait}s (attempt {attempt}) …")
            time.sleep(wait)

        except anthropic.APIConnectionError as exc:
            logger.error(f"Connection error: {exc}")
            raise

    raise RuntimeError("LLM service unavailable after retries.")

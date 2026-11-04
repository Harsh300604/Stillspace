# mentoring.md: Session 4 - First LLM call and memory
"""One function that talks to the language model: chat_completion().

It works with any OpenAI-compatible server (OpenRouter, Together AI, Ollama),
so switching provider or model only means editing .env.
"""

import re
import time

from openai import OpenAI, OpenAIError

from backend import config


class LLMError(Exception):
    """The model could not be reached or refused the request (wrong key, bad model name, no internet)."""


# Qwen3 models may "think out loud" inside <think>...</think> before answering.
# That text is not meant for the user, so it is always removed.
THINK_BLOCK = re.compile(r"<think>.*?(</think>|$)", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str) -> str:
    """Remove <think> blocks (also an unfinished one cut off by max_tokens) and trim spaces."""
    return THINK_BLOCK.sub("", text or "").strip()


def _make_client() -> OpenAI:
    """Create the API client: timeout from .env and one retry, so a dropped connection is retried once."""
    return OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY,
                  timeout=config.LLM_TIMEOUT_SECONDS, max_retries=1)


def _thinking_off(messages: list[dict], model: str) -> tuple[list[dict], dict]:
    """Ask the provider not to spend tokens on hidden reasoning (spec section 8).

    - OpenRouter understands {"reasoning": {"enabled": false}}.
    - Qwen3 models also understand "/no_think" at the end of the system message,
      which works on any provider, including Ollama.
    Thinking that slips through anyway is removed by strip_thinking().
    """
    extra_body = {"reasoning": {"enabled": False}} if "openrouter.ai" in config.LLM_BASE_URL else {}
    if "qwen3" in model.lower() and messages and messages[0]["role"] == "system":
        messages = [{"role": "system", "content": messages[0]["content"] + "\n/no_think"}] + messages[1:]
    return messages, extra_body


def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 300,
                    model: str | None = None) -> dict:
    """Send chat messages to the model and return {"text", "model", "latency_ms"}.

    `messages` is the usual list of {"role": "system"|"user"|"assistant", "content": "..."}.
    Raises LLMError with the real reason so the caller can log it and show the
    user a friendly message instead. "text" may be empty; the caller decides
    what to do then.
    """
    model = model or config.LLM_MODEL
    messages, extra_body = _thinking_off(messages, model)
    started = time.perf_counter()
    try:
        response = _make_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body or None,
        )
    except OpenAIError as error:
        raise LLMError(f"{type(error).__name__}: {error}") from error
    latency_ms = int((time.perf_counter() - started) * 1000)

    choice = response.choices[0] if response.choices else None
    text = choice.message.content if choice and choice.message else ""
    return {"text": strip_thinking(text), "model": response.model or model, "latency_ms": latency_ms}

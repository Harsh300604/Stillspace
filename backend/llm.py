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
    """Remove thinking text and trim spaces.

    Handles three shapes seen in practice:
      - "<think>...</think> answer"   (normal)
      - "<think>... (cut off)"         (max_tokens reached while thinking -> empty)
      - "... thinking ...</think> answer"  (some Ollama templates drop the opening tag)
    """
    text = text or ""
    lower = text.lower()
    if "</think>" in lower and "<think>" not in lower:
        text = text[lower.rindex("</think>") + len("</think>"):]
    return THINK_BLOCK.sub("", text).strip()


def _make_client() -> OpenAI:
    """Create the API client: timeout from .env and one retry, so a dropped connection is retried once."""
    return OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY,
                  timeout=config.LLM_TIMEOUT_SECONDS, max_retries=1)


def _thinking_off(messages: list[dict], model: str) -> tuple[list[dict], dict]:
    """Ask the provider not to spend tokens on hidden reasoning (spec section 8).

    - OpenRouter understands {"reasoning": {"enabled": false}}.
    - Ollama understands {"think": false} (tested on Ollama 0.40, D-39).
    - Hybrid Qwen3 models also understand "/no_think" at the end of a message.
    Some models always think whatever you send (e.g. Qwen3 "thinking-2507"), so
    use an instruct model; strip_thinking() removes anything that slips through.
    """
    url = config.LLM_BASE_URL.lower()
    if "openrouter.ai" in url:
        extra_body = {"reasoning": {"enabled": False}}
    elif "11434" in url or "ollama" in url:
        extra_body = {"think": False}
    else:
        extra_body = {}  # unknown provider: send nothing it might reject
    if needs_no_think(model) and messages:
        # Put the switch on the system message if there is one, otherwise on the
        # last message (the classifier sends a single user message, D-43).
        index = 0 if messages[0]["role"] == "system" else len(messages) - 1
        messages = [dict(m) for m in messages]  # copy, so the caller's list is not changed
        messages[index]["content"] += "\n/no_think"
    return messages, extra_body


def needs_no_think(model: str) -> bool:
    """Only hybrid Qwen3 models (e.g. qwen3:8b, qwen/qwen3-14b) use "/no_think".

    Instruct builds never think and thinking builds always think, so they get nothing.
    """
    name = model.lower()
    return "qwen3" in name and "instruct" not in name and "thinking" not in name


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

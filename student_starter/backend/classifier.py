# mentoring.md: Session 7 - Classifier prompt
"""The strategy classifier (spec section 11.3).

One AI call at temperature 0 reads the new message (plus recent history) and
returns JSON: which support strategy fits, plus emotion, intensity, stage and
risk. The answer is checked carefully, because small models sometimes add
extra text, wrap JSON in code fences, or invent values.
"""

import json
import re
import time

from pydantic import BaseModel

from backend import config, llm, mock

EMOTIONS = ["sadness", "anxiety", "anger", "fear", "shame", "loneliness", "stress",
            "frustration", "confusion", "neutral", "positive"]
STAGES = ["exploration", "comforting", "action"]


class ClassifierResult(BaseModel):
    """The final, typed shape every classifier answer must have."""
    strategy: str
    emotion: str
    intensity: int
    stage: str
    risk: str
    confidence: float
    rationale: str


def fallback_result(strategy_names: list[str]) -> dict:
    """Safe defaults when the model cannot be used (spec 11.3). Keyword safety still protects this path."""
    return {"strategy": strategy_names[0], "emotion": "neutral", "intensity": 3, "stage": "exploration",
            "risk": "none", "confidence": 0.0, "rationale": "classifier unavailable"}


def extract_json_object(text: str) -> dict:
    """Find the first {...} in the model's text and parse it. Raises ValueError if there is none."""
    text = llm.strip_thinking(text)
    text = re.sub(r"```(?:json)?", "", text)  # remove code fences
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object in the answer")
    depth = 0
    for position in range(start, len(text)):  # walk to the matching closing brace
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:position + 1])
    raise ValueError("JSON object is not closed")


def clean_risk(value) -> str:
    """Map risk to none/low/high. Anything unclear (e.g. 'medium') counts as high: safety first."""
    value = str(value).strip().lower()
    if value in ("none", "no", "null", ""):
        return "none"
    if value in ("low", "minimal", "mild"):
        return "low"
    return "high"


def clamp(number, low, high, default):
    """Turn number-like text into a number inside [low, high]."""
    try:
        return max(low, min(high, float(number)))
    except (TypeError, ValueError):
        return default


def parse_classifier_output(text: str, strategy_names: list[str]) -> dict:
    """Turn the model's raw answer into a clean result dict, or raise ValueError.

    TODO (Session 7): make messy model answers safe. Steps:
      1. raw = extract_json_object(text)        (already written above: finds the first {...})
      2. Strategy: match raw["strategy"] to strategy_names ignoring upper/lower case;
         if it matches nothing, use strategy_names[0].
      3. Emotion must be in EMOTIONS, stage in STAGES; otherwise "neutral" / "exploration".
      4. intensity: round(clamp(raw.get("intensity"), 1, 5, 3)); confidence: clamp(..., 0.0, 1.0, 0.0)
      5. risk: clean_risk(raw.get("risk", "none"))   (anything unclear becomes "high": safety first)
      6. rationale: str(raw.get("rationale", "")).strip()[:300]
      7. Build ClassifierResult(...) with these values and return result.model_dump().
    Done when: python scripts/eval_classifier.py shows "(llm, ...ms)" on every row.
    """
    raise ValueError("TODO Session 7: parse_classifier_output is not written yet")


def format_history(history: list[dict]) -> str:
    """Show earlier messages as 'User: ...' / 'Stillspace: ...' lines."""
    if not history:
        return "(no earlier messages)"
    names = {"user": "User", "assistant": "Stillspace"}
    return "\n".join(f"{names.get(m['role'], m['role'])}: {m['content']}" for m in history)


def build_classifier_prompt(message: str, history: list[dict], strategies: list[dict]) -> str:
    """Fill prompts/classifier.txt. .replace() is used because the template contains JSON braces."""
    template = (config.PROMPTS_DIR / "classifier.txt").read_text(encoding="utf-8").strip()
    strategy_list = "\n".join(f"- {s['name']}: {s['description']}" for s in strategies)
    return (template.replace("{strategy_list}", strategy_list)
                    .replace("{emotions}", ", ".join(EMOTIONS))
                    .replace("{history}", format_history(history))
                    .replace("{message}", message))


def classify(message: str, history: list[dict], strategies: list[dict]) -> dict:
    """Classify one message. Always returns a complete result with two extra keys:

    "source": "llm" (model answer parsed), "mock" (mock rules) or "fallback" (defaults used)
    "latency_ms": time taken

    TODO (Session 7): ask the model, with one retry. Steps:
      1. names = the strategy names; remember the start time.
      2. Mock mode (config.is_mock_mode()) is already done below: keep it.
      3. Otherwise build the prompt: [{"role": "user", "content": build_classifier_prompt(message, history, strategies)}]
      4. Try at most twice: llm.chat_completion(prompt, temperature=0, max_tokens=200,
         model=config.CLASSIFIER_MODEL), then parse_classifier_output(answer["text"], names).
         On llm.LLMError or ValueError print the error and try again.
      5. If both attempts failed: fallback_result(names), source "fallback".
      6. Add "source" and "latency_ms" to the result and return it.
    Also write the classifier prompt in backend/data/prompts/classifier.txt (see the TODOs there).
    Done when: in the chat the side panel shows a strategy chosen by the model, and
    python scripts/eval_classifier.py prints an accuracy.
    """
    names = [s["name"] for s in strategies]
    started = time.perf_counter()
    if config.is_mock_mode():
        result, source = mock.mock_classify(message, names), "mock"
    else:
        # Safe placeholder until Session 7: default values, so the chat still works.
        print("[TODO Session 7] classifier.classify is not written yet - using default values")
        result, source = fallback_result(names), "fallback"
    result.update({"source": source, "latency_ms": int((time.perf_counter() - started) * 1000)})
    return result

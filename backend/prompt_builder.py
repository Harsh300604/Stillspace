# mentoring.md: Session 9 - Prompt builder
"""Builds the messages sent to the model for a reply (spec section 11.4).

The result is [system, ...history, user]. The system message is
prompts/system.txt with the strategy, the classifier's meta details and
(optionally) check-in context filled in.

Privacy rule: only today's mood and the PHQ-9 severity BAND may go into the
prompt. Raw PHQ answers and the date of birth never do.
"""

from backend import config


def checkin_lines(checkin_context: dict) -> str:
    """Lines like "- Mood today: Low" for the prompt, or "" when switched off or there is no data."""
    if not config.INCLUDE_CHECKINS_IN_PROMPT:
        return ""
    lines = []
    if checkin_context.get("mood"):
        lines.append(f"- Mood today: {checkin_context['mood']}")
    if checkin_context.get("phq_band"):
        lines.append(f"- Recent wellbeing questionnaire: {checkin_context['phq_band']} range")
    return "\n".join(lines)


def build_system_prompt(strategy: dict, meta: dict, checkin_context: dict) -> str:
    """Fill prompts/system.txt. .replace() keeps it simple and safe with any text."""
    template = (config.PROMPTS_DIR / "system.txt").read_text(encoding="utf-8").strip()
    extra = checkin_lines(checkin_context)
    if not extra:
        template = template.replace("\n{checkin_lines}", "")  # no empty line when there is no data
    return (template.replace("{strategy_name}", strategy["name"])
                    .replace("{strategy_instruction}", strategy["instruction"])
                    .replace("{emotion}", str(meta.get("emotion", "neutral")))
                    .replace("{intensity}", str(meta.get("intensity", 3)))
                    .replace("{stage}", str(meta.get("stage", "exploration")))
                    .replace("{checkin_lines}", extra))


def build_messages(strategy: dict, meta: dict, checkin_context: dict,
                   history: list[dict], message: str) -> list[dict]:
    """Return the full chat for the model: system prompt, earlier messages, new message."""
    system = {"role": "system", "content": build_system_prompt(strategy, meta, checkin_context)}
    return [system, *history, {"role": "user", "content": message}]

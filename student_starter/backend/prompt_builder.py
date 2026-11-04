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
    """Fill prompts/system.txt. .replace() keeps it simple and safe with any text.

    TODO (Session 9): fill the template. Steps:
      1. template = (config.PROMPTS_DIR / "system.txt").read_text(encoding="utf-8").strip()
      2. extra = checkin_lines(checkin_context)   (already written above)
         If extra is empty, remove "\n{checkin_lines}" from the template (no empty line).
      3. Replace {strategy_name}, {strategy_instruction} (from `strategy`),
         {emotion}, {intensity}, {stage} (from `meta`, with defaults "neutral", 3, "exploration")
         and {checkin_lines} (with extra). Return the result.
    Done when: the DEBUG print in routes/chat.py shows a prompt with the strategy and emotion.
    """
    # Safe placeholder until Session 9: the plain prompt without any strategy.
    return (config.PROMPTS_DIR / "plain_system.txt").read_text(encoding="utf-8").strip()


def build_messages(strategy: dict, meta: dict, checkin_context: dict,
                   history: list[dict], message: str) -> list[dict]:
    """Return the full chat for the model: system prompt, earlier messages, new message.

    TODO (Session 4): add the conversation history between the system message and
    the new message, so the model remembers what was said: [system, *history, user].
    TODO (Session 9): use build_system_prompt(strategy, meta, checkin_context) for the
    system message (it uses the plain prompt until you write it).
    """
    # Safe placeholder: plain system prompt + the new message only (no memory yet).
    system = {"role": "system", "content": build_system_prompt(strategy, meta, checkin_context)}
    return [system, {"role": "user", "content": message}]

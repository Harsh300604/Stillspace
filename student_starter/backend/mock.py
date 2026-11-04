# mentoring.md: Session 4 - First LLM call and memory
"""Mock mode: canned replies so the app works with no internet and no API key.

Mock mode is on when MOCK_MODE=true or LLM_API_KEY is empty (spec section 11.7).
The replies come from the mentor's mockup, reworded so they no longer call
themselves examples. mock_classify() picks a strategy with simple keyword rules.
"""

import time

MOCK_LATENCY_SECONDS = 0.6  # feels like a real reply and lets the typing indicator show

MOCK_REPLIES = {
    "Validation": [
        "It makes sense to want space to talk about what is on your mind. What would you like to feel understood about?",
        "That sounds like a lot to hold, and it is understandable that it is weighing on you. What has felt hardest about it?",
    ],
    "Reflection": [
        "Sometimes it helps to slow down and name the part that feels most important. What would you like to explore?",
        "It sounds like a few different feelings are mixed together right now. Which part stands out most when you think about it?",
    ],
    "Reassurance": [
        "You do not have to figure everything out in this moment. What would feel supportive right now?",
        "It is clear you are taking this seriously, and that care says something good about you. One hard moment does not decide everything that comes next.",
    ],
    "Advice": [
        "If you would like a practical step, you could pause and choose one small thing within your control. Would you prefer to explore a next step or keep talking?",
        "One small option could be to write down what is worrying you most and pick the easiest piece to start with. Does that feel doable today?",
    ],
}

# Used when no strategy is chosen yet (Phase 4) or the strategy has no canned reply
# (e.g. the ESConv 8-strategy set): cycle through every reply above.
ALL_REPLIES = [reply for replies in MOCK_REPLIES.values() for reply in replies]


def mock_reply(strategy: str | None, turn: int) -> dict:
    """Return a canned reply after a short pause, in the same shape as llm.chat_completion().

    `turn` (how many replies the session already has) picks a different reply
    each time, so a mock conversation does not repeat the same sentence.
    """
    started = time.perf_counter()
    time.sleep(MOCK_LATENCY_SECONDS)
    replies = MOCK_REPLIES.get(strategy or "", ALL_REPLIES)
    text = replies[turn % len(replies)]
    return {"text": text, "model": "mock", "latency_ms": int((time.perf_counter() - started) * 1000)}


# ---------- mock classifier (spec 11.7) ----------

ADVICE_WORDS = ["what should i", "what do i do", "what can i do", "how do i", "how can i", "how should i",
                "tips", "ideas", "advice", "help me figure", "what would you suggest", "next step",
                "small way to", "where do i start"]
WORRY_WORDS = ["worried", "worry", "anxious", "nervous", "scared", "afraid", "panic", "what if",
               "going to fail", "useless", "stupid", "not good enough", "never going to", "ruin"]
UNCLEAR_WORDS = ["don't know", "dont know", "not sure", "confused", "mixed", "weird", "feel off",
                 "idk", "unsure", "can't tell", "cant tell", "something feels"]

# The rules name the 4 default strategies. For another strategy set, use the
# closest name in that set (ESConv-8 here), otherwise the set's first strategy.
CLOSEST_NAMES = {
    "Advice": ["Advice", "Providing Suggestions"],
    "Reassurance": ["Reassurance", "Affirmation and Reassurance"],
    "Reflection": ["Reflection", "Reflection of Feelings", "Restatement or Paraphrasing"],
    "Validation": ["Validation", "Reflection of Feelings"],
}


def mock_classify(message: str, strategy_names: list[str]) -> dict:
    """Pick a strategy with keyword rules and return fixed meta values (no AI involved)."""
    text = message.lower()
    if any(word in text for word in ADVICE_WORDS):
        rule, emotion, stage = "Advice", "stress", "action"
    elif any(word in text for word in WORRY_WORDS):
        rule, emotion, stage = "Reassurance", "anxiety", "comforting"
    elif any(word in text for word in UNCLEAR_WORDS):
        rule, emotion, stage = "Reflection", "confusion", "exploration"
    else:
        rule, emotion, stage = "Validation", "sadness", "exploration"
    strategy = next((name for name in CLOSEST_NAMES[rule] if name in strategy_names), strategy_names[0])
    return {"strategy": strategy, "emotion": emotion, "intensity": 3, "stage": stage, "risk": "none",
            "confidence": 0.5, "rationale": f"mock rule: {rule.lower()} keywords"}

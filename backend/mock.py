# mentoring.md: Session 4 - First LLM call and memory
"""Mock mode: canned replies so the app works with no internet and no API key.

Mock mode is on when MOCK_MODE=true or LLM_API_KEY is empty (spec section 11.7).
The replies come from the mentor's mockup, reworded so they no longer call
themselves examples. Phase 6 adds mock_classify() here.
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

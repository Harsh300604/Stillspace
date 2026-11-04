# mentoring.md: Session 5 - Safety layer
"""The deterministic safety layer (spec section 11.5).

This check runs BEFORE any AI call. If a message matches a crisis word, the
AI is never asked: the person gets a fixed reply with helpline numbers. So the
safety layer works in mock mode, offline, and when the AI model is broken.

Nothing in here should ever be weakened to make something else work.
"""

import json
import re
from functools import lru_cache

from backend import config

HELPLINES = config.HELPLINES  # one source for the numbers (implementation.md D-06)
KEYWORDS_FILE = config.BACKEND_DATA_DIR / "crisis_keywords.json"

# Common look-alike swaps used to dodge filters: k1ll -> kill, $uicide -> suicide.
# "!" is deliberately NOT swapped: "I want to die!" must still match "die".
LOOKALIKES = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def normalise(text: str) -> str:
    """Lower-case and tidy text so small spelling tricks do not hide crisis words."""
    text = text.casefold()
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = text.replace("'", "")  # "can't" and "cant" become the same
    # Look-alike swaps only inside words that also contain letters, so "112" stays "112".
    text = re.sub(r"[a-z0-9@$]*[a-z][a-z0-9@$]*", lambda m: m.group().translate(LOOKALIKES), text)
    text = re.sub(r"(?<=[a-z])[.\-_*]+(?=[a-z])", "", text)  # s.u.i.c.i.d.e -> suicide
    # d i e / k i l l -> die / kill: three or more single letters separated by spaces are joined.
    text = re.sub(r"\b(?:[a-z] ){2,}[a-z]\b", lambda m: m.group().replace(" ", ""), text)
    return re.sub(r"\s+", " ", text).strip()


def variants(text: str) -> list[str]:
    """Versions of the text to check: as typed, and with stretched letters shortened.

    "dieee" -> "die" and "killlll" -> "kill" need different shortening, so both are tried.
    """
    base = normalise(text)
    to_two = re.sub(r"(.)\1{2,}", r"\1\1", base)
    to_one = re.sub(r"(.)\1{2,}", r"\1", base)
    return list(dict.fromkeys([base, to_two, to_one]))  # unique, order kept


@lru_cache(maxsize=1)
def load_rules() -> list[tuple[str, re.Pattern]]:
    """Read crisis_keywords.json once and turn every entry into a compiled pattern."""
    with open(KEYWORDS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    rules = []
    for phrase in data["phrases"]:
        text = normalise(phrase["text"])
        if text.isascii():
            # Whole words only, so "suicide" does not match inside another word.
            rules.append((phrase["id"], re.compile(r"\b" + re.escape(text) + r"\b")))
        else:
            # Devanagari vowel signs break \b, so these phrases match as plain text.
            rules.append((phrase["id"], re.compile(re.escape(text))))
    for pattern in data["patterns"]:
        rules.append((pattern["id"], re.compile(pattern["regex"])))
    return rules


def find_crisis_match(text: str) -> str | None:
    """Return the id of the first crisis rule that matches, or None."""
    for version in variants(text):
        for rule_id, rule in load_rules():
            if rule.search(version):
                return rule_id
    return None


def check_message(text: str) -> bool:
    """True if the message contains crisis wording and must get the fixed crisis reply."""
    return find_crisis_match(text) is not None


def crisis_response() -> str:
    """The fixed crisis reply from prompts/crisis_response.txt (no AI involved)."""
    template = (config.PROMPTS_DIR / "crisis_response.txt").read_text(encoding="utf-8").strip()
    followup = ""
    if config.FOLLOWUP_CONTACT:
        followup = f"You can also contact {config.FOLLOWUP_CONTACT}, who follows up on safety concerns in this study.\n\n"
    return template.replace("{followup_line}", followup)


def phq_item9_flag(phq_answers: dict) -> bool:
    """PHQ-9 item 9 (thoughts of self-harm) above 0 needs a human follow-up, whatever the total."""
    return phq_answers.get("8", 0) > 0

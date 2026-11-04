# mentoring.md: Session 13 - Evaluation design
"""Generate replies for a human rating study: no strategy (A) vs full pipeline (B).

Run from the project folder:
    python scripts/eval_responses.py --limit 5
    python scripts/eval_responses.py --models qwen3:4b-instruct-2507-q4_K_M,ollama:qwen3:8b
    python scripts/eval_responses.py --summarise exports/rating_sheet_YYYYMMDD_HHMM_blind.csv

For every test message and every model it makes two replies:
    A = plain prompt (prompts/plain_system.txt), no strategy
    B = full pipeline: classifier -> strategy -> strategy prompt (as in the chat)
Neither condition gets chat history or check-in context, so the ONLY difference
is the strategy layer. The keyword safety check applies to both.

Two files are written to exports/:
    responses_<time>.csv          everything, incl. condition, model and strategy (for analysis)
    rating_sheet_<time>_blind.csv shuffled, WITHOUT condition/model/strategy (give this to raters)
Raters fill in empathy_1to5, strategy_followed_yes_no and safe_yes_no in the
blind sheet. "Strategy followed" is judged against the test set's expected
strategy for every row, so A and B are measured with the same yardstick.
"""

import argparse
import csv
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

# Let "import backend" work when this file is run as a script from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import classifier, config, llm, mock, prompt_builder, safety, strategy_policy  # noqa: E402

TEST_FILE = PROJECT_ROOT / "eval" / "test_messages.csv"
EXPORT_DIR = PROJECT_ROOT / "exports"
RATING_COLUMNS = ["empathy_1to5", "strategy_followed_yes_no", "safe_yes_no", "notes"]
DEFAULT_PROVIDER = (config.LLM_BASE_URL, config.LLM_API_KEY)  # from .env, restored for every non-ollama model


def use_model(name: str) -> str:
    """Point the app's settings at one model. "ollama:<model>" means the local Ollama server.

    The pipeline functions read their settings from config, so switching them
    here makes classifier, prompt builder and LLM all use this model.
    """
    config.LLM_BASE_URL, config.LLM_API_KEY = DEFAULT_PROVIDER
    if name.startswith("ollama:"):
        name = name[len("ollama:"):]
        config.LLM_BASE_URL, config.LLM_API_KEY = "http://localhost:11434/v1", "ollama"
    config.LLM_MODEL = config.CLASSIFIER_MODEL = name
    return name


def reply_text(prompt: list[dict], strategy: str | None, turn: int) -> dict:
    """One reply: mock in mock mode, otherwise the model. Errors become a visible row, not a crash."""
    if config.is_mock_mode():
        return {**mock.mock_reply(strategy, turn), "source": "mock"}
    try:
        result = llm.chat_completion(prompt, temperature=0.7, max_tokens=300)
        return {**result, "source": "llm" if result["text"] else "fallback"}
    except llm.LLMError as error:
        print(f"    model error: {error}")
        return {"text": f"[ERROR: {error}]", "model": config.LLM_MODEL, "latency_ms": 0, "source": "error"}


def condition_a(message: str, turn: int) -> dict:
    """A: plain prompt, no strategy (the same prompt as Phase 4's basic chat)."""
    plain = (config.PROMPTS_DIR / "plain_system.txt").read_text(encoding="utf-8").strip()
    result = reply_text([{"role": "system", "content": plain}, {"role": "user", "content": message}], None, turn)
    return {"reply": result["text"], "source": result["source"], "latency_ms": result["latency_ms"]}


def condition_b(message: str, strategies: list[dict], turn: int) -> dict:
    """B: the chat pipeline without history or check-ins: classify -> choose -> build prompt -> reply."""
    started = time.perf_counter()
    meta = classifier.classify(message, [], strategies)
    if meta["risk"] == "high":
        return {**meta, "reply": safety.crisis_response(), "source": "safety", "safety_flag": "classifier",
                "classified_strategy": meta["strategy"], "used_strategy": "Safety",
                "latency_ms": int((time.perf_counter() - started) * 1000)}
    used = strategy_policy.choose_strategy("Automatic", meta["strategy"], "none", [s["name"] for s in strategies])
    strategy = next(s for s in strategies if s["name"] == used)
    prompt = prompt_builder.build_messages(strategy, meta, {}, [], message)
    result = reply_text(prompt, used, turn)
    return {"reply": result["text"], "source": result["source"], "classified_strategy": meta["strategy"],
            "used_strategy": used, "emotion": meta["emotion"], "intensity": meta["intensity"],
            "stage": meta["stage"], "risk": meta["risk"], "latency_ms": int((time.perf_counter() - started) * 1000)}


def generate(rows: list[dict], models: list[str]) -> list[dict]:
    """Make the A and B reply for every message and model."""
    strategies = config.load_strategies()
    results = []
    for model_name in models:
        model = use_model(model_name)
        mode = "MOCK (no AI)" if config.is_mock_mode() else f"{model} at {config.LLM_BASE_URL}"
        print(f"\nModel: {mode}")
        for turn, row in enumerate(rows):
            for condition in ("A", "B"):
                rule = safety.find_crisis_match(row["message"])  # keyword safety applies to both conditions
                if rule:
                    out = {"reply": safety.crisis_response(), "source": "safety", "safety_flag": "keyword", "latency_ms": 0}
                else:
                    out = condition_a(row["message"], turn) if condition == "A" else condition_b(row["message"], strategies, turn)
                print(f"  {row['id']} {condition} {out.get('used_strategy', '-'):<12} {out['source']:<8} {out['latency_ms']}ms")
                results.append({"id": row["id"], "message": row["message"], "strategy_to_check": row["expected_strategy"],
                                "model": model_name, "condition": "A_no_strategy" if condition == "A" else "B_pipeline",
                                "classified_strategy": out.get("classified_strategy", ""), "used_strategy": out.get("used_strategy", ""),
                                "emotion": out.get("emotion", ""), "intensity": out.get("intensity", ""), "stage": out.get("stage", ""),
                                "risk": out.get("risk", ""), "safety_flag": out.get("safety_flag", "none"),
                                "source": out["source"], "latency_ms": out["latency_ms"], "reply": out["reply"]})
    return results


def save(results: list[dict], seed: int) -> None:
    """Write the full file and the shuffled blind rating sheet, linked by item_id."""
    EXPORT_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    shuffled = results[:]
    random.Random(seed).shuffle(shuffled)  # fixed seed: the same order can be re-created
    for number, row in enumerate(shuffled, start=1):
        row["item_id"] = f"R{number:03d}"
    full = sorted(shuffled, key=lambda r: (r["model"], r["id"], r["condition"]))
    write_csv(EXPORT_DIR / f"responses_{stamp}.csv", full, ["item_id"] + [k for k in full[0] if k != "item_id"] + RATING_COLUMNS)
    write_csv(EXPORT_DIR / f"rating_sheet_{stamp}_blind.csv", shuffled,
              ["item_id", "message", "strategy_to_check", "reply"] + RATING_COLUMNS)
    print(f"\nSaved {len(results)} rows:\n  exports/responses_{stamp}.csv  (full, for analysis)"
          f"\n  exports/rating_sheet_{stamp}_blind.csv  (shuffled, give this to raters)")


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    """CSV with the Excel marker (utf-8-sig); missing columns stay empty."""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    """Read a CSV saved by this script or by Excel (which may save in Windows encoding)."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"Could not read {path}")


def share(answers: list[str]) -> str:
    """Percentage of answers that start with "y" (yes), or "-" if nothing was rated."""
    return f"{sum(a.startswith('y') for a in answers) / len(answers):.0%}" if answers else "-"


def summarise(blind_path: Path) -> None:
    """Join the rated blind sheet with its responses file and print results per model and condition."""
    responses_path = blind_path.with_name(blind_path.name.replace("rating_sheet_", "responses_").replace("_blind", ""))
    if not responses_path.exists():
        raise SystemExit(f"Matching responses file not found: {responses_path}")
    ratings = {r["item_id"]: r for r in read_csv(blind_path)}
    groups = defaultdict(list)
    for row in read_csv(responses_path):
        groups[(row["model"], row["condition"])].append(ratings.get(row["item_id"], {}))
    print(f"{'model':<34} {'condition':<14} {'rated':>5} {'empathy':>8} {'followed':>9} {'safe':>6}")
    for (model, condition), rated in sorted(groups.items()):
        empathy = [float(r["empathy_1to5"]) for r in rated if r.get("empathy_1to5", "").strip()]
        followed = [r["strategy_followed_yes_no"].strip().lower() for r in rated if r.get("strategy_followed_yes_no", "").strip()]
        safe = [r["safe_yes_no"].strip().lower() for r in rated if r.get("safe_yes_no", "").strip()]
        mean = f"{sum(empathy) / len(empathy):.2f}" if empathy else "-"
        print(f"{model:<34} {condition:<14} {len(empathy):>5} {mean:>8} {share(followed):>9} {share(safe):>6}")


def main() -> None:
    """Parse options and either generate replies or summarise a rated sheet."""
    parser = argparse.ArgumentParser(description="Reply evaluation: no strategy (A) vs pipeline (B).")
    parser.add_argument("--limit", type=int, help="only use the first N test messages")
    parser.add_argument("--models", help="comma-separated model names; prefix ollama: for the local Ollama server")
    parser.add_argument("--seed", type=int, default=42, help="shuffle seed for the blind sheet (default 42)")
    parser.add_argument("--summarise", type=Path, help="a rated rating_sheet_*_blind.csv to summarise")
    args = parser.parse_args()
    if args.summarise:
        summarise(args.summarise)
        return
    with open(TEST_FILE, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[:args.limit]
    models = [m.strip() for m in args.models.split(",")] if args.models else [config.LLM_MODEL]
    print(f"Reply evaluation | {len(rows)} messages x {len(models)} model(s) x 2 conditions = {len(rows) * len(models) * 2} rows")
    save(generate(rows, models), args.seed)


if __name__ == "__main__":
    main()

# mentoring.md: Session 8 - Testing the classifier
"""Measure how well the classifier picks the expected strategy.

Run from the project folder:
    python scripts/eval_classifier.py            (all 30 messages)
    python scripts/eval_classifier.py --limit 5  (quick try)

It prints accuracy, a per-strategy table, a confusion table and how often each
strategy was predicted (an LLM picking the same strategy for everything is the
"preference bias" problem from the research). Results go to
exports/classifier_results.csv, which opens in Excel.
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

# Let "import backend" work when this file is run as a script from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import classifier, config  # noqa: E402  (must come after the path line above)

TEST_FILE = PROJECT_ROOT / "eval" / "test_messages.csv"
RESULTS_FILE = PROJECT_ROOT / "exports" / "classifier_results.csv"


def load_test_messages(limit: int | None) -> list[dict]:
    """Read eval/test_messages.csv (utf-8-sig removes the BOM Excel likes)."""
    with open(TEST_FILE, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def run(rows: list[dict], strategies: list[dict]) -> list[dict]:
    """Classify every message on its own (no history) and collect the results."""
    results = []
    for number, row in enumerate(rows, start=1):
        result = classifier.classify(row["message"], [], strategies)
        correct = result["strategy"] == row["expected_strategy"]
        print(f"  {number:>2}/{len(rows)} {row['id']} expected={row['expected_strategy']:<12} "
              f"predicted={result['strategy']:<12} {'OK ' if correct else 'X  '} ({result['source']}, {result['latency_ms']}ms)")
        results.append({
            "id": row["id"], "message": row["message"], "expected": row["expected_strategy"],
            "predicted": result["strategy"], "correct": "yes" if correct else "no",
            "emotion": result["emotion"], "intensity": result["intensity"], "stage": result["stage"],
            "risk": result["risk"], "confidence": result["confidence"], "rationale": result["rationale"],
            "source": result["source"], "latency_ms": result["latency_ms"],
        })
    return results


def print_report(results: list[dict], names: list[str]) -> None:
    """Accuracy, per-strategy table, confusion table and prediction counts."""
    total = len(results)
    correct = sum(r["correct"] == "yes" for r in results)
    print(f"\nAccuracy: {correct}/{total} = {correct / total:.0%}")

    print("\nPer strategy        correct/expected  precision  recall")
    for name in names:
        expected = [r for r in results if r["expected"] == name]
        predicted = [r for r in results if r["predicted"] == name]
        hits = sum(r["predicted"] == name for r in expected)
        precision = f"{hits / len(predicted):.0%}" if predicted else "-"
        recall = f"{hits / len(expected):.0%}" if expected else "-"
        print(f"  {name:<18} {hits:>3}/{len(expected):<12} {precision:>9}  {recall:>6}")

    short = [n[:11] for n in names]
    print("\nConfusion table (rows = expected, columns = predicted)")
    print("  " + " " * 13 + " ".join(f"{s:>11}" for s in short))
    for name in names:
        counts = [sum(r["expected"] == name and r["predicted"] == other for r in results) for other in names]
        print(f"  {name[:12]:<13}" + " ".join(f"{c:>11}" for c in counts))

    spread = Counter(r["predicted"] for r in results)
    print("\nHow often each strategy was predicted (preference bias check):")
    for name in names:
        print(f"  {name:<18} {spread.get(name, 0):>3}")
    if len(spread) == 1:
        print("  WARNING: every message got the same strategy (preference bias).")
    fallbacks = sum(r["source"] == "fallback" for r in results)
    if fallbacks:
        print(f"\nNote: {fallbacks} message(s) used fallback defaults (model unreachable or answer not valid JSON).")


def save_results(results: list[dict]) -> None:
    """Write the CSV (utf-8-sig so Excel shows every character correctly)."""
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved {len(results)} rows to {RESULTS_FILE}")


def main() -> None:
    """Parse options, run the evaluation, print and save the results."""
    parser = argparse.ArgumentParser(description="Evaluate the strategy classifier.")
    parser.add_argument("--limit", type=int, help="only use the first N test messages")
    args = parser.parse_args()

    strategies = config.load_strategies()
    names = [s["name"] for s in strategies]
    mode = "MOCK classifier (keyword rules, no AI)" if config.is_mock_mode() else f"model {config.CLASSIFIER_MODEL} at {config.LLM_BASE_URL}"
    print(f"Classifier evaluation | {mode} | strategy set: {config.STRATEGY_SET}")
    rows = load_test_messages(args.limit)
    unknown = {r["expected_strategy"] for r in rows} - set(names)
    if unknown:
        print(f"WARNING: the test set expects strategies not in {config.STRATEGY_SET}: {sorted(unknown)}. "
              "eval/test_messages.csv is labelled for strategies_4; set STRATEGY_SET=strategies_4 for a fair score.")
    results = run(rows, strategies)
    print_report(results, names)
    save_results(results)


if __name__ == "__main__":
    main()

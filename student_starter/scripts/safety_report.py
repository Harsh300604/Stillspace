# mentoring.md: Session 5 - Safety layer
"""List every safety flag for the follow-up review (D-51).

Run from the project folder (with DATABASE_URL set, it reads Supabase):
    python scripts/safety_report.py --days 1
    python scripts/safety_report.py --since 2026-11-01

Shows time, participant code and flag type only, never the message text, so
the report can be shared with the named follow-up adult. Flag types:
    keyword    a crisis word matched (detail = the rule id)
    classifier the classifier said risk = high
    phq_item9  PHQ-9 item 9 (thoughts of self-harm) answered above 0
"""

import argparse
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Let "import backend" work when this file is run as a script from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import config, db  # noqa: E402


def main() -> None:
    """Print the safety flags since the chosen date."""
    parser = argparse.ArgumentParser(description="List safety flags for follow-up.")
    parser.add_argument("--days", type=int, default=7, help="look back this many days (default 7)")
    parser.add_argument("--since", help="start date YYYY-MM-DD (overrides --days)")
    args = parser.parse_args()
    since = (datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since
             else datetime.now(timezone.utc) - timedelta(days=args.days))
    with closing(db.get_connection()) as conn:
        events = db.safety_events(conn, since.isoformat(timespec="seconds"))
    print(f"Safety flags since {since:%Y-%m-%d %H:%M} UTC in {db.describe()}: {len(events)}")
    print(f"Follow-up contact: {config.FOLLOWUP_CONTACT or '(FOLLOWUP_CONTACT not set!)'}")
    for event in events:
        print(f"  {event['time']}  {event['code']:<16} {event['type']:<11} {event['detail']}")
    if not events:
        print("  (none)")


if __name__ == "__main__":
    main()

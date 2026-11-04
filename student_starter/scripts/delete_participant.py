# mentoring.md: Session 11 - Check-ins and data ethics
"""Delete one participant and all their data (the right to withdraw).

Run from the project folder (with DATABASE_URL set, it deletes from Supabase):
    python scripts/delete_participant.py SS-7K3M-Q9TX

It asks for confirmation first. Deleted data cannot be recovered (except from a
backup), so double-check the code. Exports made earlier still contain the old
data: delete or update those files too.
"""

import sys
from contextlib import closing
from pathlib import Path

# Let "import backend" work when this file is run as a script from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import db  # noqa: E402


def main() -> None:
    """Look up the code, confirm, delete, report."""
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/delete_participant.py <participant code> [--yes]")
    code = sys.argv[1].strip().upper()
    with closing(db.get_connection()) as conn:
        participant = db.get_participant(conn, code)
        if participant is None:
            raise SystemExit(f"No participant with code {code} in {db.describe()}.")
        if "--yes" not in sys.argv:
            answer = input(f"Delete {code} and ALL their check-ins, sessions and messages from {db.describe()}? Type yes: ")
            if answer.strip().lower() != "yes":
                raise SystemExit("Nothing deleted.")
        counts = db.delete_participant_data(conn, participant["id"])
        conn.commit()
    print(f"Deleted {code}: " + ", ".join(f"{n} {table}" for table, n in counts.items()))
    print("Remember to delete or update any earlier export files that contain this participant.")


if __name__ == "__main__":
    main()

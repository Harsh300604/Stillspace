# mentoring.md: Session 11 - Check-ins and data ethics
"""Export every database table to a CSV file in exports/ (one file per table).

Run from the project folder:
    python scripts/export_data.py

The files open in Excel. They contain participant data (check-ins, PHQ-9,
messages), so keep them on this computer: exports/ is git-ignored on purpose.
"""

import csv
import sys
from contextlib import closing
from pathlib import Path

# Let "import backend" work when this file is run as a script from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import config, db  # noqa: E402  (must come after the path line above)

TABLES = ["participants", "checkins", "sessions", "messages"]
EXPORT_DIR = PROJECT_ROOT / "exports"


def export_table(conn, table: str) -> int:
    """Write one table to exports/<table>.csv and return how many rows were written."""
    cursor = conn.execute(f"SELECT * FROM {table} ORDER BY id")  # table names come from our own list
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    # utf-8-sig adds the marker Excel needs to show Hinglish/Devanagari text correctly (D-17).
    with open(EXPORT_DIR / f"{table}.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows([tuple(row) for row in rows])
    return len(rows)


def main() -> None:
    """Export all tables and print a short report."""
    if not config.DB_PATH.exists():
        print(f"No database found at {config.DB_PATH}. Start the app once to create it.")
        return
    EXPORT_DIR.mkdir(exist_ok=True)
    print(f"Exporting {config.DB_PATH}")
    with closing(db.get_connection()) as conn:
        for table in TABLES:
            count = export_table(conn, table)
            print(f"  {table + '.csv':<18} {count:>5} rows")
    print(f"Saved to {EXPORT_DIR}")
    print("Reminder: these files contain participant data. Keep them private and never commit them.")


if __name__ == "__main__":
    main()

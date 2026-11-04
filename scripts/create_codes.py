# mentoring.md: Session 16 - Final demo / buffer (going online)
"""Create random participant codes for the online version (D-48).

Run from the project folder (with DATABASE_URL set, codes go to Supabase):
    python scripts/create_codes.py --count 20

Online (APP_ENV=production) ONLY codes created here can sign in. They are long
and random (e.g. SS-7K3M-Q9TX), so nobody can guess someone else's code.
Hand each code to one participant privately. The list is also saved to
exports/ (git-ignored); treat it like a password list.
"""

import argparse
import csv
import secrets
import sys
import time
from contextlib import closing
from pathlib import Path

# Let "import backend" work when this file is run as a script from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import db  # noqa: E402

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I/L: easy to read out and type


def new_code(prefix: str) -> str:
    """A code like SS-7K3M-Q9TX: 8 random characters (about 850 billion possibilities)."""
    chars = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"{prefix}-{chars[:4]}-{chars[4:]}"


def main() -> None:
    """Create the codes, store them as participants, print and save the list."""
    parser = argparse.ArgumentParser(description="Create random participant codes.")
    parser.add_argument("--count", type=int, default=10, help="how many codes (default 10)")
    parser.add_argument("--prefix", default="SS", help="letters before the code (default SS)")
    args = parser.parse_args()

    db.create_tables()
    codes = []
    with closing(db.get_connection()) as conn:
        while len(codes) < args.count:
            code = new_code(args.prefix.upper())
            if db.get_participant(conn, code) is None:  # practically never taken, but check anyway
                db.create_participant(conn, code)
                codes.append(code)
        conn.commit()

    out = PROJECT_ROOT / "exports" / f"issued_codes_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "given_to (fill in privately)", "date_given"])
        writer.writerows([[code, "", ""] for code in codes])
    print(f"Created {len(codes)} codes in {db.describe()}:")
    for code in codes:
        print(f"  {code}")
    print(f"Saved to {out}. Keep this list private.")


if __name__ == "__main__":
    main()

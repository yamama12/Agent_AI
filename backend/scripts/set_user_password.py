import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.security import hash_password
from database.db import SessionLocal
from database.models import User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update a user password from plaintext and store the bcrypt hash."
    )
    parser.add_argument("--email", help="Login/email of the user to update.")
    parser.add_argument("--id", type=int, help="Numeric user id to update.")
    parser.add_argument("--password", required=True, help="Plaintext password to hash and save.")
    parser.add_argument(
        "--force-change",
        action="store_true",
        help="Mark the user to change the password on next login.",
    )
    args = parser.parse_args()

    if not args.email and args.id is None:
        parser.error("Provide --email or --id.")

    return args


def main() -> int:
    args = parse_args()
    password = args.password.strip()

    if len(password) < 6:
        print("Password must contain at least 6 characters.")
        return 1

    session = SessionLocal()
    try:
        query = session.query(User)
        if args.id is not None:
            user = query.filter(User.id == args.id).first()
        else:
            user = query.filter(User.email == args.email.strip()).first()

        if user is None:
            print("User not found.")
            return 1

        user.password = hash_password(password)
        if args.force_change:
            user.changepassword = True

        session.add(user)
        session.commit()
        session.refresh(user)

        print(f"Password updated for user id={user.id}, email={user.email}.")
        print(f"Stored hash length: {len(user.password)}")
        print(f"Hash prefix: {user.password[:7]}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

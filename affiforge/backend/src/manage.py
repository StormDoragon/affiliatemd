"""Operator commands for account provisioning and recovery."""

import argparse
from getpass import getpass

from pydantic import ValidationError

from .crud.users import create_user, get_user_by_email
from .db import SessionLocal
from .schemas.user import UserCreate
from .security import get_password_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["create-user", "reset-password"])
    parser.add_argument("email")
    parser.add_argument("--name", default="AffiForge user")
    args = parser.parse_args()

    password = getpass("Password: ")
    if password != getpass("Confirm password: "):
        parser.exit(1, "Passwords do not match.\n")
    try:
        payload = UserCreate(email=args.email, full_name=args.name, password=password)
    except ValidationError:
        parser.exit(1, "Use a valid email and a password of 12 to 128 characters.\n")

    with SessionLocal() as db:
        existing = get_user_by_email(db, args.email)
        if args.operation == "create-user":
            if existing:
                parser.exit(1, "This account already exists.\n")
            create_user(db, payload)
        else:
            if not existing:
                parser.exit(1, "Account not found.\n")
            existing.hashed_password = get_password_hash(payload.password)
            db.commit()
    print("Account updated.")


if __name__ == "__main__":
    main()

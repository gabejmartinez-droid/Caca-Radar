#!/usr/bin/env python3
"""One-off privileged account provisioning for controlled environments.

This script is the manual alternative to startup seeding. It should be run
explicitly when you want to (re)provision the admin, demo municipality, or
App Review accounts with credentials from the environment.
"""

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from server import provision_privileged_accounts, client  # noqa: E402


ACCOUNT_CHOICES = ("admin", "demo_muni", "review")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision privileged accounts from environment credentials."
    )
    parser.add_argument(
        "--account",
        action="append",
        choices=ACCOUNT_CHOICES,
        help="Limit provisioning to one or more specific accounts.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    selected_accounts = set(args.account or [])
    try:
        seeded = await provision_privileged_accounts(selected_accounts or None)
        if not seeded:
            print("No privileged accounts were provisioned.")
            return 0
        print("Privileged accounts provisioned:")
        if "admin_email" in seeded:
            print(f"- Admin: {seeded['admin_email']}")
        if "demo_muni_email" in seeded:
            print(f"- Demo municipality: {seeded['demo_muni_email']}")
        if "review_email" in seeded:
            print(f"- App Review: {seeded['review_email']} / {seeded['review_username']}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

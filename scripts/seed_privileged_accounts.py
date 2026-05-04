#!/usr/bin/env python3
"""One-off privileged account provisioning for controlled environments.

This script is the manual alternative to startup seeding. It should be run
explicitly when you want to (re)provision the admin, demo municipality, or
App Review accounts with credentials from the environment.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from server import provision_privileged_accounts, client  # noqa: E402


async def main() -> int:
    try:
        seeded = await provision_privileged_accounts()
        if not seeded:
            print("No privileged accounts were provisioned.")
            return 0
        print("Privileged accounts provisioned:")
        print(f"- Admin: {seeded['admin_email']}")
        print(f"- Demo municipality: {seeded['demo_muni_email']}")
        print(f"- App Review: {seeded['review_email']} / {seeded['review_username']}")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

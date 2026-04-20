#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RELEASE_PREPARE = ROOT / "scripts" / "release_prepare.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bump tracked versions, append an audit entry, and then run a build command."
    )
    parser.add_argument(
        "--surface",
        action="append",
        choices=["web", "ios", "android", "backend"],
        required=True,
        help="Surface to bump before the build. Repeat for multiple surfaces.",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Optional audit-log note. Repeat for multiple bullets.",
    )
    parser.add_argument(
        "--status",
        default="pending",
        choices=["pending", "released"],
        help="Version-history entry status.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run after version tracking. Prefix with --.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.command or args.command[0] != "--" or len(args.command) == 1:
        raise SystemExit("Pass the build command after --, for example: -- yarn run build:raw")

    command = args.command[1:]

    prep_command = [sys.executable, str(RELEASE_PREPARE), "--status", args.status]
    seen = set()
    for surface in args.surface:
        if surface in seen:
            continue
        seen.add(surface)
        prep_command.append(f"--bump-{surface}")

    if args.note:
        for note in args.note:
            prep_command.extend(["--notes", note])
    else:
        prep_command.extend(["--notes", f"Automated build for: {', '.join(seen)}"])

    subprocess.run(prep_command, cwd=ROOT, check=True)
    completed = subprocess.run(command, cwd=ROOT / "frontend")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERSION_FILES = {
    "frontend/src/appVersions.json",
    "frontend/android/app/build.gradle",
    "frontend/ios/App/App.xcodeproj/project.pbxproj",
    "memory/VERSION_HISTORY.md",
}

IGNORED_PREFIXES = (
    ".githooks/",
    "docs/",
    "family-workout-app/",
    "frontend/android/app/build/",
    "frontend/ios/App/CapacitorPushNotifications/.swiftpm/",
    "scripts/",
)

IGNORED_EXACT = {
    ".DS_Store",
}

IOS_RELEVANT_PREFIXES = (
    "frontend/src/",
    "frontend/public/",
    "frontend/ios/",
    "frontend/capacitor.config.json",
)

ANDROID_RELEVANT_PREFIXES = (
    "frontend/src/",
    "frontend/public/",
    "frontend/android/",
    "frontend/capacitor.config.json",
)

BACKEND_RELEVANT_PREFIXES = (
    "backend/",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def is_ignored(path: str) -> bool:
    if path in IGNORED_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in IGNORED_PREFIXES)


def matches_prefixes(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def main() -> int:
    staged = [
        line.strip()
        for line in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines()
        if line.strip()
    ]

    relevant = [path for path in staged if not is_ignored(path)]
    if not relevant:
        return 0

    non_version_relevant = [path for path in relevant if path not in VERSION_FILES]
    if not non_version_relevant:
        return 0

    missing: list[str] = []
    staged_set = set(staged)

    # Always keep the shared version ledger in sync when shipping code.
    if "frontend/src/appVersions.json" not in staged_set:
        missing.append("frontend/src/appVersions.json")
    if "memory/VERSION_HISTORY.md" not in staged_set:
        missing.append("memory/VERSION_HISTORY.md")

    if any(matches_prefixes(path, IOS_RELEVANT_PREFIXES) for path in non_version_relevant):
        if "frontend/ios/App/App.xcodeproj/project.pbxproj" not in staged_set:
            missing.append("frontend/ios/App/App.xcodeproj/project.pbxproj")

    if any(matches_prefixes(path, ANDROID_RELEVANT_PREFIXES) for path in non_version_relevant):
        if "frontend/android/app/build.gradle" not in staged_set:
            missing.append("frontend/android/app/build.gradle")

    # Backend version lives in appVersions + version history, so no extra file required here.
    if any(matches_prefixes(path, BACKEND_RELEVANT_PREFIXES) for path in non_version_relevant):
        pass

    if not missing:
        return 0

    unique_missing = list(dict.fromkeys(missing))
    sys.stderr.write("\nVersion guard blocked this commit.\n\n")
    sys.stderr.write("You staged app/backend changes without the matching version files:\n")
    for path in unique_missing:
        sys.stderr.write(f"  - {path}\n")
    sys.stderr.write(
        "\nRun the release prep helper before committing, for example:\n"
        "  python3 scripts/release_prepare.py --bump-ios --bump-android --notes \"Describe the change\"\n"
        "\nFor backend-only work, bump the backend version instead:\n"
        "  python3 scripts/release_prepare.py --bump-backend --notes \"Describe the change\"\n\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

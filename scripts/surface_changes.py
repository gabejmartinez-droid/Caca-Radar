from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IGNORED_PREFIXES = (
    "family-workout-app/",
    "frontend/build/",
    "frontend/node_modules/",
)

IGNORED_FILES = {
    "frontend/src/appVersions.json",
    "memory/VERSION_HISTORY.md",
}

SHARED_FRONTEND_PREFIXES = (
    "frontend/src/",
    "frontend/public/",
)

SHARED_FRONTEND_FILES = {
    "frontend/package.json",
    "frontend/capacitor.config.json",
    "frontend/craco.config.js",
    "frontend/package-lock.json",
    "frontend/yarn.lock",
}

SPECIAL_DIFF_FILTERS = {
    "frontend/package.json": ('"version": ',),
    "frontend/android/app/build.gradle": ("versionCode ", 'versionName "'),
    "frontend/ios/App/App.xcodeproj/project.pbxproj": ("CURRENT_PROJECT_VERSION = ", "MARKETING_VERSION = "),
}


def changed_entries(root: Path = ROOT) -> list[tuple[str, str]]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
        )
    except Exception:
        return []

    entries: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        path = raw_path.strip()
        if path:
            entries.append((status, path))
    return entries


def has_meaningful_diff(path: str, root: Path = ROOT) -> bool:
    filters = SPECIAL_DIFF_FILTERS.get(path)
    if not filters:
        return True
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--no-ext-diff", "HEAD", "--", path],
            cwd=root,
            text=True,
        )
    except Exception:
        return True

    for line in diff.splitlines():
        if not line or line.startswith(("+++", "---", "@@")):
            continue
        if not line.startswith(("+", "-")):
            continue
        if line.startswith(("+++", "---")):
            continue
        content = line[1:].strip()
        if any(content.startswith(prefix) for prefix in filters):
            continue
        return True
    return False


def classify_changed_surfaces(root: Path = ROOT) -> set[str]:
    surfaces: set[str] = set()
    for status, path in changed_entries(root):
        if path in IGNORED_FILES or path.startswith(IGNORED_PREFIXES):
            continue
        if path in SPECIAL_DIFF_FILTERS and not status.startswith("??") and not has_meaningful_diff(path, root):
            continue

        if path in SHARED_FRONTEND_FILES or path.startswith(SHARED_FRONTEND_PREFIXES):
            surfaces.update({"web", "ios", "android"})
            continue

        if path.startswith("frontend/ios/"):
            surfaces.add("ios")
            continue

        if path.startswith("frontend/android/"):
            surfaces.add("android")
            continue

        if path.startswith("backend/"):
            surfaces.add("backend")

    return surfaces

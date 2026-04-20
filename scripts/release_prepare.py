#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_VERSIONS_PATH = ROOT / "frontend" / "src" / "appVersions.json"
PACKAGE_JSON_PATH = ROOT / "frontend" / "package.json"
ANDROID_BUILD_GRADLE_PATH = ROOT / "frontend" / "android" / "app" / "build.gradle"
IOS_PBXPROJ_PATH = ROOT / "frontend" / "ios" / "App" / "App.xcodeproj" / "project.pbxproj"
VERSION_HISTORY_PATH = ROOT / "memory" / "VERSION_HISTORY.md"

WEB_BACKEND_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)-(?P<kind>web|api)\.(?P<rev>\d+)$")
SEMVER_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a Caca Radar release by bumping platform versions and appending a version-history entry."
    )
    parser.add_argument("--date", default=str(date.today()), help="Entry date in YYYY-MM-DD format")
    parser.add_argument("--status", default="pending", choices=["pending", "released"], help="History entry status")
    parser.add_argument("--notes", action="append", default=[], help="Release note bullet. Repeat for multiple bullets.")
    parser.add_argument("--commit", help="Optional commit hash to include in the history entry")
    parser.add_argument("--bundle-hash", help="Optional production frontend bundle hash to include in the history entry")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing files")

    parser.add_argument("--bump-web", action="store_true", help="Auto-bump the web version")
    parser.add_argument("--bump-ios", action="store_true", help="Auto-bump the iOS version/build")
    parser.add_argument("--bump-android", action="store_true", help="Auto-bump the Android version/build")
    parser.add_argument("--bump-backend", action="store_true", help="Auto-bump the backend version")

    parser.add_argument("--set-web", help="Explicit web version, e.g. 1.1.2-web.1")
    parser.add_argument("--set-ios-version", help="Explicit iOS marketing version, e.g. 1.1.2")
    parser.add_argument("--set-ios-build", type=int, help="Explicit iOS build number")
    parser.add_argument("--set-android-version", help="Explicit Android versionName, e.g. 1.1.2")
    parser.add_argument("--set-android-build", type=int, help="Explicit Android versionCode")
    parser.add_argument("--set-backend", help="Explicit backend version, e.g. 1.1.1-api.1")
    return parser.parse_args()


def bump_web_or_backend(version: str) -> str:
    match = WEB_BACKEND_RE.match(version)
    if not match:
        raise ValueError(f"Unsupported version format: {version}")
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch")) + 1
    kind = match.group("kind")
    rev = match.group("rev")
    return f"{major}.{minor}.{patch}-{kind}.{rev}"


def bump_semver(version: str) -> str:
    match = SEMVER_RE.match(version)
    if not match:
        raise ValueError(f"Unsupported semver format: {version}")
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch")) + 1
    return f"{major}.{minor}.{patch}"


def replace_one(text: str, pattern: str, replacement: str) -> str:
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected to replace exactly one match for pattern: {pattern}")
    return new_text


def build_history_entry(args: argparse.Namespace, versions: dict, changed_envs: list[str]) -> str:
    status_text = "Released" if args.status == "released" else "Pending deploy"
    commit_text = f" `{args.commit}`" if args.commit else ""
    lines = [
        f"### {args.date} — {status_text}{commit_text}",
        "",
        "Impacted environments:",
    ]
    for env in changed_envs:
        if env == "web":
            lines.append(f"- Web `{versions['web']}`")
        elif env == "ios":
            lines.append(f"- iOS `{versions['ios']['version']} ({versions['ios']['build']})`")
        elif env == "android":
            lines.append(f"- Android `{versions['android']['version']} ({versions['android']['build']})`")
        elif env == "backend":
            lines.append(f"- Backend `{versions['backend']}`")
    lines.append("")
    lines.append("Changes:")
    if args.notes:
        for note in args.notes:
            lines.append(f"- {note}")
    else:
        lines.append("- Version bump prepared with the automated release script.")
    if args.bundle_hash:
        lines.extend(["", f"Bundle hash: `{args.bundle_hash}`"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    if not any([
        args.bump_web,
        args.bump_ios,
        args.bump_android,
        args.bump_backend,
        args.set_web,
        args.set_ios_version,
        args.set_ios_build is not None,
        args.set_android_version,
        args.set_android_build is not None,
        args.set_backend,
    ]):
        raise SystemExit("Nothing to do. Pass at least one bump or set flag.")

    versions = json.loads(APP_VERSIONS_PATH.read_text())
    package_json = json.loads(PACKAGE_JSON_PATH.read_text())
    android_gradle = ANDROID_BUILD_GRADLE_PATH.read_text()
    ios_pbxproj = IOS_PBXPROJ_PATH.read_text()
    version_history = VERSION_HISTORY_PATH.read_text()

    changed_envs: list[str] = []

    if args.bump_web or args.set_web:
        versions["web"] = args.set_web or bump_web_or_backend(versions["web"])
        package_json["version"] = versions["web"]
        changed_envs.append("web")

    if args.bump_ios or args.set_ios_version or args.set_ios_build is not None:
        if args.bump_ios and not args.set_ios_version:
            versions["ios"]["version"] = bump_semver(versions["ios"]["version"])
        elif args.set_ios_version:
            versions["ios"]["version"] = args.set_ios_version

        if args.bump_ios and args.set_ios_build is None:
            versions["ios"]["build"] = str(int(versions["ios"]["build"]) + 1)
        elif args.set_ios_build is not None:
            versions["ios"]["build"] = str(args.set_ios_build)
        changed_envs.append("ios")

    if args.bump_android or args.set_android_version or args.set_android_build is not None:
        if args.bump_android and not args.set_android_version:
            versions["android"]["version"] = bump_semver(versions["android"]["version"])
        elif args.set_android_version:
            versions["android"]["version"] = args.set_android_version

        if args.bump_android and args.set_android_build is None:
            versions["android"]["build"] = str(int(versions["android"]["build"]) + 1)
        elif args.set_android_build is not None:
            versions["android"]["build"] = str(args.set_android_build)
        changed_envs.append("android")

    if args.bump_backend or args.set_backend:
        versions["backend"] = args.set_backend or bump_web_or_backend(versions["backend"])
        changed_envs.append("backend")

    if "android" in changed_envs:
        android_gradle = replace_one(
            android_gradle,
            r"versionCode\s+\d+",
            f"versionCode {versions['android']['build']}",
        )
        android_gradle = replace_one(
            android_gradle,
            r'versionName\s+"[^"]+"',
            f'versionName "{versions["android"]["version"]}"',
        )

    if "ios" in changed_envs:
        ios_pbxproj = re.sub(
            r"CURRENT_PROJECT_VERSION = \d+;",
            f"CURRENT_PROJECT_VERSION = {versions['ios']['build']};",
            ios_pbxproj,
        )
        ios_pbxproj = re.sub(
            r"MARKETING_VERSION = \d+\.\d+\.\d+;",
            f"MARKETING_VERSION = {versions['ios']['version']};",
            ios_pbxproj,
        )

    history_entry = build_history_entry(args, versions, changed_envs)
    version_history = version_history.rstrip() + "\n\n" + history_entry + "\n"

    if args.dry_run:
        print("Planned versions:")
        print(json.dumps(versions, indent=2))
        print("\nHistory entry:\n")
        print(history_entry)
        return 0

    APP_VERSIONS_PATH.write_text(json.dumps(versions, indent=2) + "\n")
    PACKAGE_JSON_PATH.write_text(json.dumps(package_json, indent=2) + "\n")
    ANDROID_BUILD_GRADLE_PATH.write_text(android_gradle)
    IOS_PBXPROJ_PATH.write_text(ios_pbxproj)
    VERSION_HISTORY_PATH.write_text(version_history)

    print("Updated versions:")
    print(json.dumps(versions, indent=2))
    print("\nAppended history entry:\n")
    print(history_entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from surface_changes import classify_changed_surfaces

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
IOS_APP = FRONTEND / "ios" / "App"
ANDROID_DIR = FRONTEND / "android"
RELEASE_PREPARE = ROOT / "scripts" / "release_prepare.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bump native versions for the selected platform bundle rebuild and run the necessary build steps."
    )
    parser.add_argument(
        "--surface",
        choices=["ios", "android", "mobile"],
        required=True,
        help="Which platform bundle(s) to rebuild.",
    )
    return parser.parse_args()


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def bump_versions(surface: str) -> None:
    changed_surfaces = classify_changed_surfaces(ROOT)
    cmd = [sys.executable, str(RELEASE_PREPARE), "--status", "pending"]
    should_bump_ios = surface in {"ios", "mobile"} and "ios" in changed_surfaces
    should_bump_android = surface in {"android", "mobile"} and "android" in changed_surfaces
    if should_bump_ios:
        cmd.extend(["--bump-ios", "--notes", "Rebuilt iOS bundle"])
    if should_bump_android:
        cmd.extend(["--bump-android", "--notes", "Rebuilt Android bundle"])
    if should_bump_ios or should_bump_android:
        run(cmd, ROOT)


def rebuild_shared_assets() -> None:
    run(["yarn", "run", "build:mobile:raw"], FRONTEND)


def rebuild_ios() -> None:
    run(
        [
            "xcodebuild",
            "-project",
            "App.xcodeproj",
            "-scheme",
            "App",
            "-configuration",
            "Debug",
            "-sdk",
            "iphoneos",
            "-destination",
            "generic/platform=iOS",
            "CODE_SIGNING_ALLOWED=NO",
            "build",
        ],
        IOS_APP,
    )


def rebuild_android() -> None:
    env = os.environ.copy()
    java_home = "/Applications/Android Studio.app/Contents/jbr/Contents/Home"
    env["JAVA_HOME"] = java_home
    env["PATH"] = f"{java_home}/bin:{env.get('PATH', '')}"
    env["GRADLE_USER_HOME"] = "/tmp/cacaradar-gradle87"
    subprocess.run(["./gradlew", "bundleRelease"], cwd=ANDROID_DIR, check=True, env=env)


def main() -> int:
    args = parse_args()
    bump_versions(args.surface)
    rebuild_shared_assets()
    if args.surface in {"ios", "mobile"}:
        rebuild_ios()
    if args.surface in {"android", "mobile"}:
        rebuild_android()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Export MongoDB collections to timestamped gzip JSONL files.

Run with the same environment variables as the backend:
MONGO_URL, DB_NAME, and optionally BACKUP_DIR.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient


DEFAULT_COLLECTIONS = [
    "users",
    "reports",
    "report_audit_log",
    "votes",
    "validations",
    "report_votes",
    "flags",
    "municipalities",
    "subscription_receipts",
    "webhook_notifications",
]


def json_default(value: Any) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def redacted_mongo_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{host}{port}"


def export_collection(db, collection_name: str, output_path: Path) -> int:
    count = 0
    with gzip.open(output_path, "wt", encoding="utf-8") as handle:
        for doc in db[collection_name].find({}):
            handle.write(json.dumps(doc, default=json_default, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Export Caca Radar MongoDB data.")
    parser.add_argument("--output-dir", default=os.environ.get("BACKUP_DIR", "backups"))
    parser.add_argument("--collections", nargs="*", default=DEFAULT_COLLECTIONS)
    args = parser.parse_args()

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir) / f"{db_name}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)

    client = MongoClient(mongo_url)
    db = client[db_name]

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "db_name": db_name,
        "mongo_url": redacted_mongo_url(mongo_url),
        "collections": {},
    }

    for collection_name in args.collections:
        output_path = output_dir / f"{collection_name}.jsonl.gz"
        count = export_collection(db, collection_name, output_path)
        manifest["collections"][collection_name] = {
            "count": count,
            "file": output_path.name,
        }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": "ok", "output_dir": str(output_dir), **manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Caca Radar Data Protection Runbook

Production user reports must never be stored in a local container database. Preview
environments can be recreated or restored from old snapshots, so they are only for
testing.

## Required Production Environment

Set these variables on the production backend:

```bash
APP_ENV=production
MONGO_URL=mongodb+srv://...
DB_NAME=cacaradar_production
GIT_SHA=<deployed commit sha>
```

The backend refuses to start in production if `MONGO_URL` points at localhost or if
`DB_NAME` is a known test/development name.

Use separate databases:

```text
cacaradar_dev
cacaradar_staging
cacaradar_production
```

## Verification Endpoints

Public:

```http
GET /api/version
GET /api/health/deep
```

Admin-only:

```http
GET /api/admin/report-diagnostics
GET /api/admin/report-audit
```

Cartagena recovery/query example:

```http
GET /api/admin/report-diagnostics?lat_min=37.55&lat_max=37.75&lng_min=-1.10&lng_max=-0.85
```

## Report Audit Trail

Every `POST /api/reports` now writes to `report_audit_log` as well as `reports`.
The audit event includes:

- user id/email/username
- report id
- latitude/longitude
- municipality/province
- request IP/user-agent/origin
- app version/platform headers when present
- environment, DB name, redacted Mongo host, and deployed commit

This collection is intentionally append-only from the application path. Use it to
prove where a report write landed.

## Manual Export

Run from the repo root or backend folder with backend env vars loaded:

```bash
cd backend
python scripts/export_database.py --output-dir ../backups
```

The script writes timestamped `.jsonl.gz` files and a `manifest.json` with counts.
Store these exports somewhere outside the app host for real production use.

## Production Deploy Checklist

Before deploy:

```bash
GET /api/health/deep on current production
Run a fresh database backup/export
Confirm APP_ENV=production
Confirm DB_NAME=cacaradar_production
Confirm MONGO_URL is not localhost
```

After deploy:

```bash
GET /api/version
GET /api/health/deep
Create one test report from the app
Confirm the report exists in reports
Confirm the matching event exists in report_audit_log
Delete or mark the test report if needed
```

## Managed Database Backups

For MongoDB Atlas, enable:

- Continuous backup or daily snapshots
- Point-in-time restore if available
- At least 7-30 days of retention
- Alerts for failed backups

The app-level export script is a second layer, not a replacement for managed
database backups.

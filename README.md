# Caca Radar

## Release helper

Use the release helper to bump the platform versions that changed and append an audit entry:

```bash
python3 scripts/release_prepare.py \
  --bump-web \
  --bump-ios \
  --bump-android \
  --notes "Map menu resized to avoid the report button" \
  --status pending
```

Preview without writing:

```bash
python3 scripts/release_prepare.py --bump-web --notes "Preview only" --dry-run
```

## Build tracking

The standard frontend build scripts now auto-bump version metadata and append to the audit log before they run:

```bash
cd frontend
yarn build
```

- bumps `web`
- updates [frontend/src/appVersions.json](/Users/gabrielmartinez/Documents/New%20project/frontend/src/appVersions.json)
- updates [memory/VERSION_HISTORY.md](/Users/gabrielmartinez/Documents/New%20project/memory/VERSION_HISTORY.md)

```bash
cd frontend
yarn build:mobile
```

- bumps `web`, `ios`, and `android`
- updates platform version files plus the audit log
- then runs the web build and `cap sync`

If you need a build without touching version metadata, use:

```bash
cd frontend
yarn build:raw
```

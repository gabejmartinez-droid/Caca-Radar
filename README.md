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

The default build scripts now bump tracked versions automatically before building:

```bash
cd frontend
yarn build
```

- bumps `web`
- updates [frontend/src/appVersions.json](/Users/gabrielmartinez/Documents/New%20project/frontend/src/appVersions.json)
- appends a structured entry to [memory/VERSION_HISTORY.md](/Users/gabrielmartinez/Documents/New%20project/memory/VERSION_HISTORY.md)
- builds the web bundle

```bash
cd frontend
yarn build:mobile
```

- bumps `web`, `ios`, and `android`
- updates platform version files plus the audit log
- builds the web bundle and runs native sync/copy steps

The release aliases point to those same versioned build flows:

```bash
cd frontend
yarn release:web
```

- same as `yarn build`

```bash
cd frontend
yarn release:mobile
```

- same as `yarn build:mobile`

If you need the underlying compile step explicitly without bumping versions, the raw paths remain available:

```bash
cd frontend
yarn build:raw
yarn build:mobile:raw
```

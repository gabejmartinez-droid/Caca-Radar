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

The safe default build scripts now compile assets without changing version metadata:

```bash
cd frontend
yarn build
```

- builds the web bundle only
- does not touch [frontend/src/appVersions.json](/Users/gabrielmartinez/Documents/New%20project/frontend/src/appVersions.json)
- does not append to [memory/VERSION_HISTORY.md](/Users/gabrielmartinez/Documents/New%20project/memory/VERSION_HISTORY.md)

```bash
cd frontend
yarn build:mobile
```

- builds the web bundle and runs `cap sync`
- does not bump any tracked versions

Use the release scripts only when you intentionally want to bump versions and append an audit entry before building:

```bash
cd frontend
yarn release:web
```

- bumps `web`
- updates [frontend/src/appVersions.json](/Users/gabrielmartinez/Documents/New%20project/frontend/src/appVersions.json)
- updates [memory/VERSION_HISTORY.md](/Users/gabrielmartinez/Documents/New%20project/memory/VERSION_HISTORY.md)

```bash
cd frontend
yarn release:mobile
```

- bumps `web`, `ios`, and `android`
- updates platform version files plus the audit log
- then runs the web build and `cap sync`

If you need the underlying compile step explicitly, `yarn build:raw` remains available.

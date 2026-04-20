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

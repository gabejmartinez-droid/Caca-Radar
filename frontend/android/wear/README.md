# Caca Radar Wear OS Companion

This folder contains a Wear OS scaffold for one-tap quick reports.

Architecture:
- the watch gets its own current GPS location
- it sends a message to the paired phone over the Wear Data Layer
- the phone app uses the synced access token to call `/api/reports/quick`
- the phone sends a result message back to the watch

This scaffold is intentionally not wired into the current Android Gradle settings yet, so it won't destabilize the main phone app build.

Next integration steps:
1. Add `include ':wear'` in `frontend/android/settings.gradle`
2. Open the Android project in Android Studio and import the module
3. Install both the phone app and wear module on paired devices
4. Validate location permission and one-tap report flow

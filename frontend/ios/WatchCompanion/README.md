# Caca Radar Apple Watch Companion

This folder contains the Apple Watch companion app for one-tap quick reports.

What it assumes:
- the user is already logged into the iPhone app
- the iPhone app has synced its access token into the native companion bridge
- the watch talks to the phone with `WatchConnectivity`
- the phone files the actual backend request through `/api/reports/quick`

Current wiring:
1. The iPhone app target already includes `WatchSessionCoordinator.swift`.
2. A standalone watchOS Xcode project now lives at `WatchCompanion/WatchCompanion.xcodeproj`.
3. The watch app uses these SwiftUI files directly from this folder.
4. Test on a paired iPhone + Apple Watch with the main app logged in.

This first pass intentionally keeps the UI simple:
- one primary button
- current GPS from the watch
- no photo flow
- success/error confirmation only

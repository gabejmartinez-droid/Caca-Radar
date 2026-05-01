# Caca Radar Apple Watch Companion

This folder contains a watchOS companion-app scaffold for one-tap quick reports.

What it assumes:
- the user is already logged into the iPhone app
- the iPhone app has synced its access token into the native companion bridge
- the watch talks to the phone with `WatchConnectivity`
- the phone files the actual backend request through `/api/reports/quick`

Recommended integration path:
1. Add a new watchOS App target in Xcode.
2. Drop these files into the watch target.
3. Keep the iPhone app target using `WatchSessionCoordinator.swift`.
4. Test on a paired iPhone + Apple Watch with the main app logged in.

This first pass intentionally keeps the UI simple:
- one primary button
- current GPS from the watch
- no photo flow
- success/error confirmation only

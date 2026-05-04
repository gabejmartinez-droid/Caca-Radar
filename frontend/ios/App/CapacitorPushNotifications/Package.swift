// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CapacitorPushNotifications",
    platforms: [.iOS(.v15)],
    products: [
        .library(
            name: "CapacitorPushNotifications",
            targets: ["PushNotificationsPlugin"])
    ],
    dependencies: [
        .package(path: "../capacitor-swift-pm-local")
    ],
    targets: [
        .target(
            name: "PushNotificationsPlugin",
            dependencies: [
                .product(name: "Capacitor", package: "capacitor-swift-pm-local"),
                .product(name: "Cordova", package: "capacitor-swift-pm-local")
            ],
            path: "Sources/PushNotificationsPlugin")
    ]
)

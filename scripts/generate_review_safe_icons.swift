import AppKit
import Foundation

struct OutputIcon {
    let path: String
    let size: Int
}

extension NSColor {
    convenience init(hex: UInt32, alpha: CGFloat = 1.0) {
        self.init(
            calibratedRed: CGFloat((hex >> 16) & 0xFF) / 255.0,
            green: CGFloat((hex >> 8) & 0xFF) / 255.0,
            blue: CGFloat(hex & 0xFF) / 255.0,
            alpha: alpha
        )
    }
}

extension NSImage {
    func writePNG(to url: URL) throws {
        guard let tiffData = tiffRepresentation,
              let imageRep = NSBitmapImageRep(data: tiffData),
              let pngData = imageRep.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "generate_review_safe_icons", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "Unable to encode PNG for \(url.path)"
            ])
        }
        try pngData.write(to: url)
    }
}

func makeRadarIcon(size: Int) -> NSImage {
    let side = CGFloat(size)
    let image = NSImage(size: NSSize(width: side, height: side))

    image.lockFocus()
    defer { image.unlockFocus() }

    let fullRect = NSRect(x: 0, y: 0, width: side, height: side)
    NSColor(hex: 0xD62828).setFill()
    fullRect.fill()

    let bandHeight = side * 0.42
    let bandRect = NSRect(x: 0, y: (side - bandHeight) / 2.0, width: side, height: bandHeight)
    NSColor(hex: 0xF4C430).setFill()
    bandRect.fill()

    let glow = NSGradient(colors: [
        NSColor(hex: 0xFFD766, alpha: 0.35),
        NSColor(hex: 0xFFD766, alpha: 0.0),
    ])
    glow?.draw(in: NSBezierPath(ovalIn: NSRect(x: side * 0.18, y: side * 0.18, width: side * 0.64, height: side * 0.64)), relativeCenterPosition: NSPoint(x: 0, y: 0))

    let radarDiameter = side * 0.56
    let radarRect = NSRect(
        x: (side - radarDiameter) / 2.0,
        y: side * 0.26,
        width: radarDiameter,
        height: radarDiameter
    )

    let radarFill = NSGradient(colors: [NSColor(hex: 0x183153), NSColor(hex: 0x0F223C)])
    radarFill?.draw(in: NSBezierPath(ovalIn: radarRect), angle: -90)

    let rimPath = NSBezierPath(ovalIn: radarRect)
    rimPath.lineWidth = max(8, side * 0.014)
    NSColor(hex: 0xF8F9FA, alpha: 0.95).setStroke()
    rimPath.stroke()

    let center = NSPoint(x: radarRect.midX, y: radarRect.midY)
    let ringLineWidth = max(4, side * 0.008)
    for factor in [1.0, 0.68, 0.36] {
        let diameter = radarDiameter * factor
        let rect = NSRect(x: center.x - diameter / 2.0, y: center.y - diameter / 2.0, width: diameter, height: diameter)
        let path = NSBezierPath(ovalIn: rect)
        path.lineWidth = ringLineWidth
        NSColor(hex: 0xFFFFFF, alpha: factor == 1.0 ? 0.26 : 0.18).setStroke()
        path.stroke()
    }

    let crosshair = NSBezierPath()
    crosshair.lineWidth = max(3, side * 0.006)
    crosshair.move(to: NSPoint(x: radarRect.minX + radarDiameter * 0.12, y: center.y))
    crosshair.line(to: NSPoint(x: radarRect.maxX - radarDiameter * 0.12, y: center.y))
    crosshair.move(to: NSPoint(x: center.x, y: radarRect.minY + radarDiameter * 0.12))
    crosshair.line(to: NSPoint(x: center.x, y: radarRect.maxY - radarDiameter * 0.12))
    NSColor(hex: 0xFFFFFF, alpha: 0.18).setStroke()
    crosshair.stroke()

    let sweepStart: CGFloat = -22
    let sweepEnd: CGFloat = 46
    let sweepPath = NSBezierPath()
    sweepPath.move(to: center)
    sweepPath.appendArc(withCenter: center, radius: radarDiameter * 0.42, startAngle: sweepStart, endAngle: sweepEnd)
    sweepPath.close()
    NSColor(hex: 0x9BF6FF, alpha: 0.24).setFill()
    sweepPath.fill()

    let sweepLine = NSBezierPath()
    sweepLine.lineWidth = max(5, side * 0.01)
    sweepLine.move(to: center)
    let sweepRadians = sweepEnd * .pi / 180.0
    sweepLine.line(to: NSPoint(
        x: center.x + cos(sweepRadians) * radarDiameter * 0.42,
        y: center.y + sin(sweepRadians) * radarDiameter * 0.42
    ))
    NSColor(hex: 0x9BF6FF, alpha: 0.95).setStroke()
    sweepLine.stroke()

    let pinHeight = side * 0.22
    let pinWidth = side * 0.14
    let pinCenterX = center.x
    let pinTopY = radarRect.minY + side * 0.06 + pinHeight
    let pinBottomY = radarRect.minY + side * 0.045
    let pinPath = NSBezierPath()
    pinPath.move(to: NSPoint(x: pinCenterX, y: pinBottomY))
    pinPath.curve(
        to: NSPoint(x: pinCenterX - pinWidth / 2.0, y: pinTopY - pinHeight * 0.32),
        controlPoint1: NSPoint(x: pinCenterX - pinWidth * 0.42, y: pinBottomY + pinHeight * 0.16),
        controlPoint2: NSPoint(x: pinCenterX - pinWidth * 0.56, y: pinTopY - pinHeight * 0.62)
    )
    pinPath.curve(
        to: NSPoint(x: pinCenterX, y: pinTopY),
        controlPoint1: NSPoint(x: pinCenterX - pinWidth / 2.0, y: pinTopY - pinHeight * 0.04),
        controlPoint2: NSPoint(x: pinCenterX - pinWidth * 0.2, y: pinTopY)
    )
    pinPath.curve(
        to: NSPoint(x: pinCenterX + pinWidth / 2.0, y: pinTopY - pinHeight * 0.32),
        controlPoint1: NSPoint(x: pinCenterX + pinWidth * 0.2, y: pinTopY),
        controlPoint2: NSPoint(x: pinCenterX + pinWidth / 2.0, y: pinTopY - pinHeight * 0.04)
    )
    pinPath.curve(
        to: NSPoint(x: pinCenterX, y: pinBottomY),
        controlPoint1: NSPoint(x: pinCenterX + pinWidth * 0.56, y: pinTopY - pinHeight * 0.62),
        controlPoint2: NSPoint(x: pinCenterX + pinWidth * 0.42, y: pinBottomY + pinHeight * 0.16)
    )
    NSColor(hex: 0xF8F9FA).setFill()
    pinPath.fill()

    let pinHoleDiameter = pinWidth * 0.34
    let pinHoleRect = NSRect(
        x: pinCenterX - pinHoleDiameter / 2.0,
        y: pinTopY - pinHeight * 0.48,
        width: pinHoleDiameter,
        height: pinHoleDiameter
    )
    NSColor(hex: 0xFF6B6B).setFill()
    NSBezierPath(ovalIn: pinHoleRect).fill()

    let centerDotRect = NSRect(x: center.x - side * 0.028, y: center.y - side * 0.028, width: side * 0.056, height: side * 0.056)
    NSColor(hex: 0xFF6B6B).setFill()
    NSBezierPath(ovalIn: centerDotRect).fill()

    return image
}

func pixelSize(from filename: String) -> Int? {
    if let range = filename.range(of: #"(\d+(\.\d+)?)x(\d+(\.\d+)?)"#, options: .regularExpression) {
        let token = String(filename[range]).split(separator: "x").first ?? ""
        let base = Double(token) ?? 0
        let scale: Double
        if filename.contains("@3x") {
            scale = 3
        } else if filename.contains("@2x") {
            scale = 2
        } else {
            scale = 1
        }
        return Int(round(base * scale))
    }
    return nil
}

func outputsFromContentsJSON(at path: String) throws -> [OutputIcon] {
    let url = URL(fileURLWithPath: path)
    let data = try Data(contentsOf: url)
    let object = try JSONSerialization.jsonObject(with: data) as? [String: Any]
    let images = object?["images"] as? [[String: Any]] ?? []
    let directory = url.deletingLastPathComponent()
    return images.compactMap { item in
        guard let filename = item["filename"] as? String else { return nil }
        guard let size = pixelSize(from: filename) else { return nil }
        return OutputIcon(path: directory.appendingPathComponent(filename).path, size: size)
    }
}

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)

let iosIconOutputs = try outputsFromContentsJSON(at: root.appendingPathComponent("frontend/ios/App/App/Assets.xcassets/AppIcon.appiconset/Contents.json").path)
let watchAssetOutputs = try outputsFromContentsJSON(at: root.appendingPathComponent("frontend/ios/WatchCompanionApp/Assets.xcassets/WatchAppIcon.appiconset/Contents.json").path)

let watchRootOutputs: [OutputIcon] = [
    "AppIcon24x24@2x.png",
    "AppIcon27.5x27.5@2x.png",
    "AppIcon29x29@2x.png",
    "AppIcon40x40@2x.png",
    "AppIcon44x44@2x.png",
    "AppIcon50x50@2x.png",
    "AppIcon54x54@2x.png",
    "AppIcon86x86@2x.png",
    "AppIcon98x98@2x.png",
    "AppIcon108x108@2x.png",
    "AppIcon117x117@2x.png",
].compactMap { name in
    guard let size = pixelSize(from: name) else { return nil }
    return OutputIcon(path: root.appendingPathComponent("frontend/ios/WatchCompanionApp/\(name)").path, size: size)
}

let publicOutputs: [OutputIcon] = [
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-16x16.png").path, size: 16),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-32x32.png").path, size: 32),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-48x48.png").path, size: 48),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-64x64.png").path, size: 64),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-128x128.png").path, size: 128),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-192.png").path, size: 192),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-192x192.png").path, size: 192),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-512.png").path, size: 512),
    OutputIcon(path: root.appendingPathComponent("frontend/public/icon-512x512.png").path, size: 512),
    OutputIcon(path: root.appendingPathComponent("frontend/public/caca-radar-icon.png").path, size: 512),
]

let allOutputs = iosIconOutputs + watchAssetOutputs + watchRootOutputs + publicOutputs
let fileManager = FileManager.default

for output in allOutputs {
    let url = URL(fileURLWithPath: output.path)
    try fileManager.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
    try makeRadarIcon(size: output.size).writePNG(to: url)
}

print("Generated \(allOutputs.count) review-safe icon assets.")

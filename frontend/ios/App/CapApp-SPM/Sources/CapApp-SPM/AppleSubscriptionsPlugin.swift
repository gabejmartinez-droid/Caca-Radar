import Capacitor
import Foundation
import StoreKit

@objc(AppleSubscriptionsPlugin)
public class AppleSubscriptionsPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "AppleSubscriptionsPlugin"
    public let jsName = "AppleSubscriptions"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "getProducts", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "purchase", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "restorePurchases", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getActiveSubscriptions", returnType: CAPPluginReturnPromise),
    ]

    @objc func getProducts(_ call: CAPPluginCall) {
        guard #available(iOS 15.0, *) else {
            call.reject("Apple subscriptions require iOS 15 or later")
            return
        }

        let productIds = normalizedProductIds(from: call)
        guard !productIds.isEmpty else {
            call.reject("Missing App Store product identifiers")
            return
        }

        Task {
            do {
                let products = try await Product.products(for: productIds)
                let orderedProducts = productIds.compactMap { productId in
                    products.first(where: { $0.id == productId })
                }
                call.resolve([
                    "products": orderedProducts.map(serializeProduct),
                ])
            } catch {
                call.reject("Failed to load App Store products", nil, error)
            }
        }
    }

    @objc func purchase(_ call: CAPPluginCall) {
        guard #available(iOS 15.0, *) else {
            call.reject("Apple subscriptions require iOS 15 or later")
            return
        }

        guard let productId = call.getString("productId")?.trimmingCharacters(in: .whitespacesAndNewlines), !productId.isEmpty else {
            call.reject("Missing App Store product identifier")
            return
        }

        Task {
            do {
                let products = try await Product.products(for: [productId])
                guard let product = products.first else {
                    call.reject("App Store product not found")
                    return
                }

                let purchaseResult = try await product.purchase()
                switch purchaseResult {
                case .success(let verification):
                    let transaction = try verified(verification)
                    let payload = serializeTransaction(transaction, status: "purchased")
                    await transaction.finish()
                    call.resolve(payload)
                case .pending:
                    call.resolve(["status": "pending"])
                case .userCancelled:
                    call.resolve(["status": "cancelled"])
                @unknown default:
                    call.resolve(["status": "unknown"])
                }
            } catch {
                call.reject("App Store purchase failed", nil, error)
            }
        }
    }

    @objc func restorePurchases(_ call: CAPPluginCall) {
        guard #available(iOS 15.0, *) else {
            call.reject("Apple subscriptions require iOS 15 or later")
            return
        }

        Task {
            do {
                try await AppStore.sync()
                let subscriptions = try await currentActiveSubscriptions()
                call.resolve([
                    "status": subscriptions.isEmpty ? "empty" : "restored",
                    "subscriptions": subscriptions,
                ])
            } catch {
                call.reject("Failed to restore App Store purchases", nil, error)
            }
        }
    }

    @objc func getActiveSubscriptions(_ call: CAPPluginCall) {
        guard #available(iOS 15.0, *) else {
            call.reject("Apple subscriptions require iOS 15 or later")
            return
        }

        Task {
            do {
                let subscriptions = try await currentActiveSubscriptions()
                call.resolve([
                    "subscriptions": subscriptions,
                ])
            } catch {
                call.reject("Failed to read App Store entitlements", nil, error)
            }
        }
    }

    private func normalizedProductIds(from call: CAPPluginCall) -> [String] {
        (call.options["productIds"] as? [String] ?? [])
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    @available(iOS 15.0, *)
    private func serializeProduct(_ product: Product) -> JSObject {
        var payload = JSObject()
        payload["id"] = product.id
        payload["displayName"] = product.displayName
        payload["description"] = product.description
        payload["displayPrice"] = product.displayPrice
        payload["type"] = serializedProductType(product.type)
        payload["hasIntroOffer"] = product.subscription?.introductoryOffer != nil
        return payload
    }

    @available(iOS 15.0, *)
    private func serializeTransaction(_ transaction: Transaction, status: String) -> JSObject {
        var payload = JSObject()
        payload["status"] = status
        payload["productId"] = transaction.productID
        payload["transactionId"] = String(transaction.id)
        payload["originalTransactionId"] = String(transaction.originalID)
        payload["purchaseDate"] = isoString(transaction.purchaseDate)
        payload["expirationDate"] = transaction.expirationDate.map(isoString)
        payload["isUpgraded"] = transaction.isUpgraded
        return payload
    }

    @available(iOS 15.0, *)
    private func currentActiveSubscriptions() async throws -> [JSObject] {
        var subscriptions: [JSObject] = []
        for await entitlement in Transaction.currentEntitlements {
            let transaction = try verified(entitlement)
            guard transaction.productType == .autoRenewable else {
                continue
            }
            subscriptions.append(serializeTransaction(transaction, status: "active"))
        }
        return subscriptions.sorted { lhs, rhs in
            let leftExpiry = lhs["expirationDate"] as? String ?? ""
            let rightExpiry = rhs["expirationDate"] as? String ?? ""
            return leftExpiry > rightExpiry
        }
    }

    @available(iOS 15.0, *)
    private func verified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .verified(let value):
            return value
        case .unverified:
            throw NSError(
                domain: "AppleSubscriptionsPlugin",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "App Store transaction could not be verified"]
            )
        }
    }

    @available(iOS 15.0, *)
    private func serializedProductType(_ type: Product.ProductType) -> String {
        switch type {
        case .consumable:
            return "consumable"
        case .nonConsumable:
            return "nonConsumable"
        case .nonRenewable:
            return "nonRenewable"
        case .autoRenewable:
            return "autoRenewable"
        default:
            return "unknown"
        }
    }

    private func isoString(_ date: Date) -> String {
        ISO8601DateFormatter().string(from: date)
    }
}

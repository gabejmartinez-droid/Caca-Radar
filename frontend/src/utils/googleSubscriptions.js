import { Capacitor, registerPlugin } from "@capacitor/core";

const GoogleSubscriptions = registerPlugin("GoogleSubscriptions");

export function isNativeGoogleSubscriptionsSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "android";
}

export async function getGoogleSubscriptionProducts(productIds) {
  if (!isNativeGoogleSubscriptionsSupported()) {
    return [];
  }
  const result = await GoogleSubscriptions.getProducts({ productIds });
  return Array.isArray(result?.products) ? result.products : [];
}

export async function purchaseGoogleSubscription(productId, options = {}) {
  if (!isNativeGoogleSubscriptionsSupported()) {
    throw new Error("Google Play subscriptions are only supported on Android");
  }
  return GoogleSubscriptions.purchase({
    productId,
    obfuscatedAccountId: options.obfuscatedAccountId || "",
  });
}

export async function restoreGoogleSubscriptions() {
  if (!isNativeGoogleSubscriptionsSupported()) {
    return { status: "unsupported", subscriptions: [] };
  }
  const result = await GoogleSubscriptions.restorePurchases();
  return {
    status: result?.status || "empty",
    subscriptions: Array.isArray(result?.subscriptions) ? result.subscriptions : [],
  };
}

export async function getActiveGoogleSubscriptions() {
  if (!isNativeGoogleSubscriptionsSupported()) {
    return [];
  }
  const result = await GoogleSubscriptions.getActiveSubscriptions();
  return Array.isArray(result?.subscriptions) ? result.subscriptions : [];
}

export async function acknowledgeGoogleSubscription(purchaseToken) {
  if (!isNativeGoogleSubscriptionsSupported() || !purchaseToken) {
    return;
  }
  await GoogleSubscriptions.acknowledgePurchase({ purchaseToken });
}

export async function openGoogleSubscriptionManagement(productId = "") {
  if (!isNativeGoogleSubscriptionsSupported()) {
    return;
  }
  await GoogleSubscriptions.openSubscriptionManagement({ productId });
}

import { Capacitor, registerPlugin } from "@capacitor/core";

const AppleSubscriptions = registerPlugin("AppleSubscriptions");

export function isNativeAppleSubscriptionsSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "ios";
}

export async function getAppleSubscriptionProducts(productIds) {
  if (!isNativeAppleSubscriptionsSupported()) {
    return [];
  }
  const result = await AppleSubscriptions.getProducts({ productIds });
  return Array.isArray(result?.products) ? result.products : [];
}

export async function purchaseAppleSubscription(productId) {
  if (!isNativeAppleSubscriptionsSupported()) {
    throw new Error("Apple subscriptions are only supported on iOS");
  }
  return AppleSubscriptions.purchase({ productId });
}

export async function restoreAppleSubscriptions() {
  if (!isNativeAppleSubscriptionsSupported()) {
    return { status: "unsupported", subscriptions: [] };
  }
  const result = await AppleSubscriptions.restorePurchases();
  return {
    status: result?.status || "empty",
    subscriptions: Array.isArray(result?.subscriptions) ? result.subscriptions : [],
  };
}

export async function getActiveAppleSubscriptions() {
  if (!isNativeAppleSubscriptionsSupported()) {
    return [];
  }
  const result = await AppleSubscriptions.getActiveSubscriptions();
  return Array.isArray(result?.subscriptions) ? result.subscriptions : [];
}

const STORAGE_KEY = "cacaRadarNativePremiumEntitlement";

export function saveNativePremiumEntitlement(entitlement) {
  if (typeof window === "undefined" || !entitlement?.store || !entitlement?.productId) {
    return null;
  }
  const payload = {
    store: entitlement.store,
    productId: entitlement.productId,
    plan: entitlement.plan || "monthly",
    purchaseToken: entitlement.purchaseToken || "",
    transactionId: entitlement.transactionId || "",
    expirationDate: entitlement.expirationDate || "",
    savedAt: new Date().toISOString(),
  };
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  return payload;
}

export function getNativePremiumEntitlement() {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const entitlement = JSON.parse(raw);
    if (!entitlement?.store || !entitlement?.productId) return null;
    if (entitlement.expirationDate && Date.parse(entitlement.expirationDate) <= Date.now()) {
      window.localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return entitlement;
  } catch {
    return null;
  }
}

export function clearNativePremiumEntitlement() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

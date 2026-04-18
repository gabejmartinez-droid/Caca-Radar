import { API, NATIVE_PUSH_ENABLED } from "../config";
import { isCapacitorNative } from "../tokenManager";
import axios from "axios";

/**
 * Push notification manager — handles Web Push (browser) and Capacitor native push.
 */

export function isNativePushAvailableForThisBuild() {
  return !isCapacitorNative() || NATIVE_PUSH_ENABLED;
}

export function getPushUnavailableReasonKey() {
  if (isCapacitorNative() && !NATIVE_PUSH_ENABLED) {
    return "mapUi.pushUnavailableOnThisBuild";
  }
  return "mapUi.pushUnsupported";
}

export async function isPushSupported() {
  if (isCapacitorNative()) {
    if (!NATIVE_PUSH_ENABLED) {
      return false;
    }
    try {
      const { PushNotifications } = await import("@capacitor/push-notifications");
      return !!PushNotifications;
    } catch {
      return false;
    }
  }
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export async function getPushPermissionState() {
  if (isCapacitorNative()) {
    if (!NATIVE_PUSH_ENABLED) {
      return "denied";
    }
    try {
      const { PushNotifications } = await import("@capacitor/push-notifications");
      const result = await PushNotifications.checkPermissions();
      return result.receive; // "prompt" | "granted" | "denied"
    } catch {
      return "denied";
    }
  }
  return Notification.permission; // "default" | "granted" | "denied"
}

export async function subscribeToPush(userLocation) {
  if (isCapacitorNative()) {
    if (!NATIVE_PUSH_ENABLED) {
      throw new Error("native_push_disabled_for_build");
    }
    return subscribeNativePush(userLocation);
  }
  return subscribeWebPush(userLocation);
}

export async function unsubscribeFromPush() {
  try {
    await axios.post(`${API}/push/unsubscribe`, {}, { withCredentials: true });
    localStorage.setItem("caca_notifications", "off");
    return true;
  } catch {
    return false;
  }
}

// ---- Web Push (browser) ----
async function subscribeWebPush(userLocation) {
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("permission_denied");
  }

  // Register service worker if needed
  let reg = await navigator.serviceWorker.getRegistration("/sw.js");
  if (!reg) {
    reg = await navigator.serviceWorker.register("/sw.js");
    await navigator.serviceWorker.ready;
  }

  const { data: vapidData } = await axios.get(`${API}/push/vapid-key`);
  if (!vapidData.vapid_public_key) {
    throw new Error("no_vapid_key");
  }

  const subscription = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: vapidData.vapid_public_key,
  });

  await axios.post(
    `${API}/push/subscribe`,
    {
      subscription: subscription.toJSON(),
      latitude: userLocation?.lat || null,
      longitude: userLocation?.lng || null,
    },
    { withCredentials: true }
  );

  localStorage.setItem("caca_notifications", "on");
  return true;
}

// ---- Native Push (Capacitor) ----
async function subscribeNativePush(userLocation) {
  try {
    const { PushNotifications } = await import("@capacitor/push-notifications");

    const permResult = await PushNotifications.requestPermissions();
    if (permResult.receive !== "granted") {
      throw new Error("permission_denied");
    }

    return new Promise((resolve, reject) => {
      let settled = false;
      let registrationListener;
      let errorListener;

      const cleanup = async () => {
        try { await registrationListener?.remove?.(); } catch {}
        try { await errorListener?.remove?.(); } catch {}
      };

      const finish = async (callback) => {
        if (settled) return;
        settled = true;
        clearTimeout(timeoutId);
        await cleanup();
        callback();
      };

      const timeoutId = setTimeout(() => {
        finish(() => reject(new Error("native_registration_timeout")));
      }, 20000);

      (async () => {
        registrationListener = await PushNotifications.addListener("registration", async (token) => {
          try {
            await axios.post(
              `${API}/push/subscribe`,
              {
                subscription: { token: token.value, platform: "native" },
                latitude: userLocation?.lat || null,
                longitude: userLocation?.lng || null,
              },
              { withCredentials: true }
            );
            localStorage.setItem("caca_notifications", "on");
            finish(() => resolve(true));
          } catch (err) {
            finish(() => reject(err));
          }
        });

        errorListener = await PushNotifications.addListener("registrationError", (err) => {
          finish(() => reject(new Error(err.error || "native_registration_failed")));
        });

        await PushNotifications.register();
      })().catch((err) => {
        finish(() => reject(err));
      });
    });
  } catch (err) {
    if (err.message === "permission_denied") throw err;
    // Capacitor plugin not available — fallback silently
    throw new Error("native_push_unavailable");
  }
}

// ---- Listeners for native push (call once in app init) ----
export async function setupNativePushListeners() {
  if (!isCapacitorNative()) return;
  if (!NATIVE_PUSH_ENABLED) return;

  try {
    const { PushNotifications } = await import("@capacitor/push-notifications");

    PushNotifications.addListener("pushNotificationReceived", (notification) => {
      // Show an in-app toast when push arrives while app is open
      if (window.__cacaToast) {
        window.__cacaToast(notification.title || "Caca Radar", {
          description: notification.body,
        });
      }
    });

    PushNotifications.addListener("pushNotificationActionPerformed", (action) => {
      const url = action.notification?.data?.url;
      if (url && window.location) {
        window.location.href = url;
      }
    });
  } catch {
    // Plugin not available
  }
}

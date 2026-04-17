import { API } from "../config";
import { isCapacitorNative } from "../tokenManager";
import axios from "axios";

/**
 * Push notification manager — handles Web Push (browser) and Capacitor native push.
 */

export async function isPushSupported() {
  if (isCapacitorNative()) {
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

    await PushNotifications.register();

    // Listen for the registration token
    return new Promise((resolve, reject) => {
      PushNotifications.addListener("registration", async (token) => {
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
          resolve(true);
        } catch (err) {
          reject(err);
        }
      });

      PushNotifications.addListener("registrationError", (err) => {
        reject(new Error(err.error || "native_registration_failed"));
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

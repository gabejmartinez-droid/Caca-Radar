import { Capacitor, registerPlugin } from "@capacitor/core";

const GoogleAuth = registerPlugin("GoogleAuth");

export function isNativeGoogleSupported() {
  return Capacitor.isNativePlatform() && ["android", "ios"].includes(Capacitor.getPlatform());
}

export function isNativeAndroidGoogleSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "android";
}

export function isNativeIOSGoogleSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "ios";
}

export async function signInWithGoogleNative({ serverClientId, iosClientId = "" }) {
  if (!isNativeGoogleSupported()) {
    throw new Error("Native Google sign-in is only supported on iOS and Android");
  }
  const payload = isNativeIOSGoogleSupported()
    ? { serverClientId, iosClientId }
    : { serverClientId };
  const result = await GoogleAuth.signIn(payload);
  return result?.idToken || "";
}

export async function signOutGoogleNative() {
  if (!isNativeGoogleSupported()) {
    return;
  }
  try {
    await GoogleAuth.signOut();
  } catch (error) {
    console.warn("Native Google sign-out failed", error);
  }
}

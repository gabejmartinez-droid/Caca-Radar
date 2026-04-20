import { Capacitor, registerPlugin } from "@capacitor/core";

const GoogleAuth = registerPlugin("GoogleAuth");

export function isNativeAndroidGoogleSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "android";
}

export async function signInWithGoogleNative(serverClientId) {
  if (!isNativeAndroidGoogleSupported()) {
    throw new Error("Native Google sign-in is only supported on Android");
  }
  const result = await GoogleAuth.signIn({ serverClientId });
  return result?.idToken || "";
}

export async function signOutGoogleNative() {
  if (!isNativeAndroidGoogleSupported()) {
    return;
  }
  try {
    await GoogleAuth.signOut();
  } catch (error) {
    console.warn("Native Google sign-out failed", error);
  }
}

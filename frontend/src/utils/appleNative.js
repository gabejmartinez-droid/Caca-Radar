import { Capacitor, registerPlugin } from "@capacitor/core";

const AppleAuth = registerPlugin("AppleAuth");

export function isNativeAppleSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "ios";
}

export async function signInWithAppleNative() {
  if (!isNativeAppleSupported()) {
    throw new Error("Native Apple sign-in is only supported on iOS");
  }
  const result = await AppleAuth.signIn();
  return {
    identityToken: result?.identityToken || "",
    authorizationCode: result?.authorizationCode || "",
    email: result?.email || "",
    givenName: result?.givenName || "",
    familyName: result?.familyName || "",
    fullName: result?.fullName || "",
    user: result?.user || "",
  };
}

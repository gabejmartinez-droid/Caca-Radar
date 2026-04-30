import { Capacitor } from "@capacitor/core";
import { API, APPLE_WEB_CLIENT_ID } from "../config";

export function isNativeAppleSupported() {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "ios";
}

export function isWebAppleSupported() {
  return typeof window !== "undefined" && !Capacitor.isNativePlatform() && Boolean(APPLE_WEB_CLIENT_ID);
}

export function isAppleSignInSupported() {
  return isNativeAppleSupported() || isWebAppleSupported();
}

export function startAppleWebAuth(flow = "login", nextPath = "/") {
  if (!isWebAppleSupported()) {
    throw new Error("Apple sign-in is not configured for the web");
  }
  const normalizedFlow = flow === "link" ? "link" : "login";
  const normalizedNextPath =
    typeof nextPath === "string" && nextPath.startsWith("/") ? nextPath : "/";
  const url = new URL(`${API}/auth/apple/start`, window.location.origin);
  url.searchParams.set("flow", normalizedFlow);
  url.searchParams.set("next", normalizedNextPath);
  window.location.assign(url.toString());
}

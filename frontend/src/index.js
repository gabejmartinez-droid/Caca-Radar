import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { isCapacitorNative } from "./tokenManager";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register the PWA service worker only for real web browsers.
// Inside Capacitor, WKWebView already serves the bundled assets locally and
// adding a service worker can slow startup and complicate auth/navigation.
if (!isCapacitorNative() && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

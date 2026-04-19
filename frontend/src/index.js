import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

const isGoogleCallbackRoute =
  typeof window !== "undefined" &&
  window.location.pathname === "/auth/google/callback";

async function handleGoogleCallbackPreboot() {
  const root = document.getElementById("root");
  if (!root) return false;

  const setMessage = (title, detail = "") => {
    root.innerHTML = `
      <div style="min-height:100vh;background:#F8F9FA;display:flex;align-items:center;justify-content:center;padding:24px;font-family:Inter,system-ui,sans-serif;">
        <div style="text-align:center;max-width:320px;">
          <div style="width:32px;height:32px;border:3px solid rgba(255,107,107,.2);border-top-color:#FF6B6B;border-radius:9999px;margin:0 auto 16px;animation:caca-spin 1s linear infinite;"></div>
          <p style="margin:0 0 8px;color:#2B2D42;font-weight:600;">${title}</p>
          ${detail ? `<p style="margin:0;color:#8D99AE;font-size:12px;line-height:1.5;">${detail}</p>` : ""}
        </div>
      </div>
      <style>
        @keyframes caca-spin { to { transform: rotate(360deg); } }
      </style>
    `;
    window.sessionStorage.setItem("google_callback_status", `${title}${detail ? ` :: ${detail}` : ""}`);
  };

  const hash = window.location.hash.replace(/^#/, "");
  const hashParams = new URLSearchParams(hash);
  const searchParams = new URLSearchParams(window.location.search);
  const sessionId = searchParams.get("session_id") || hashParams.get("session_id");

  if (!sessionId) {
    setMessage("Google callback failed", "No session ID received from Google");
    window.setTimeout(() => window.location.replace("/login"), 2000);
    return true;
  }

  if (window.location.hash) {
    window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
  }

  try {
    setMessage("Connecting to Google", "Exchanging Google session with backend");
    const response = await fetch("/api/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ session_id: sessionId }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data?.detail || "Google login failed");
    }

    setMessage("Login succeeded", "Redirecting to the map");
    window.location.replace("/?google_login=1");
    window.setTimeout(() => {
      if (window.location.pathname === "/auth/google/callback") {
        window.location.assign("/?google_login=1");
      }
    }, 250);
  } catch (error) {
    setMessage("Google callback failed", error.message || "Unable to complete Google sign-in");
    window.setTimeout(() => window.location.replace("/login"), 3000);
  }

  return true;
}

async function boot() {
  if (isGoogleCallbackRoute) {
    const handled = await handleGoogleCallbackPreboot();
    if (handled) return;
  }

  const root = ReactDOM.createRoot(document.getElementById("root"));
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

boot();

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

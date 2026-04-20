import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { getGoogleClientId, isGoogleIdentitySupported, loadGoogleIdentityScript } from "../utils/googleIdentity";
import { GOOGLE_IOS_CLIENT_ID } from "../config";
import { isNativeGoogleSupported, isNativeAndroidGoogleSupported, isNativeIOSGoogleSupported, signInWithGoogleNative } from "../utils/googleNative";

export function GoogleSignInButton({
  onCredential,
  onError,
  text = "continue_with",
  context = "signin",
  testId = "google-signin-btn",
}) {
  const { t } = useLanguage();
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [unavailableReason, setUnavailableReason] = useState("");
  const isNativeIOS = isNativeIOSGoogleSupported();
  const isNativeAndroid = isNativeAndroidGoogleSupported();
  const isNativeGoogle = isNativeGoogleSupported();

  useEffect(() => {
    let cancelled = false;

    async function setupGoogleButton() {
      const clientId = getGoogleClientId();
      if (isNativeGoogle) {
        if (!clientId || (isNativeIOS && !GOOGLE_IOS_CLIENT_ID)) {
          setUnavailableReason(t("loginUi.googleNotConfigured"));
        }
        setLoading(false);
        return;
      }
      if (!isGoogleIdentitySupported()) {
        setUnavailableReason(t("loginUi.googleBrowserOnly"));
        setLoading(false);
        return;
      }
      if (!clientId) {
        setUnavailableReason(t("loginUi.googleNotConfigured"));
        setLoading(false);
        return;
      }

      try {
        await loadGoogleIdentityScript();
        if (cancelled || !containerRef.current || !window.google?.accounts?.id) return;

        containerRef.current.innerHTML = "";
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async ({ credential }) => {
            if (!credential) {
              const error = new Error("Google login was cancelled");
              console.warn("Google sign-in popup returned no credential");
              onError?.(error);
              return;
            }
            try {
              await onCredential(credential);
            } catch (error) {
              console.error("Google sign-in handler failed", error);
              onError?.(error);
            }
          },
          context,
          cancel_on_tap_outside: true,
          use_fedcm_for_prompt: false,
        });

        window.google.accounts.id.renderButton(containerRef.current, {
          type: "standard",
          theme: "outline",
          size: "large",
          shape: "pill",
          text,
          width: containerRef.current.offsetWidth || 320,
          logo_alignment: "left",
        });

        setLoading(false);
      } catch (error) {
        if (!cancelled) {
          setUnavailableReason(t("loginUi.googleUnavailable"));
          setLoading(false);
          onError?.(error);
        }
      }
    }

    setupGoogleButton();

    return () => {
      cancelled = true;
    };
  }, [context, isNativeGoogle, isNativeIOS, onCredential, onError, t, text]);

  const handleNativeClick = async () => {
    const serverClientId = getGoogleClientId();
    if (!serverClientId || (isNativeIOS && !GOOGLE_IOS_CLIENT_ID)) {
      const error = new Error(t("loginUi.googleNotConfigured"));
      setUnavailableReason(error.message);
      onError?.(error);
      return;
    }

    setLoading(true);
    try {
      const credential = await signInWithGoogleNative({
        serverClientId,
        iosClientId: GOOGLE_IOS_CLIENT_ID,
      });
      if (!credential) {
        throw new Error(t("loginUi.googleError"));
      }
      await onCredential?.(credential);
    } catch (error) {
      console.error("Native Google sign-in failed", error);
      onError?.(error);
    } finally {
      setLoading(false);
    }
  };

  if (unavailableReason) {
    return (
      <div
        className="w-full border border-[#8D99AE]/20 rounded-xl py-3 px-4 text-sm text-[#8D99AE] text-center bg-gray-50"
        data-testid={`${testId}-unavailable`}
      >
        {unavailableReason}
      </div>
    );
  }

  if (isNativeGoogle) {
    return (
      <button
        type="button"
        onClick={handleNativeClick}
        disabled={loading}
        className="w-full min-h-[44px] border border-[#8D99AE]/20 rounded-xl py-3 px-4 text-sm text-[#2B2D42] bg-white flex items-center justify-center gap-3 disabled:opacity-70"
        data-testid={testId}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin text-[#8D99AE]" />
        ) : (
          <>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.3-1.5 3.9-5.5 3.9-3.3 0-6-2.8-6-6.2s2.7-6.2 6-6.2c1.9 0 3.1.8 3.8 1.5l2.6-2.5C16.7 2.9 14.6 2 12 2 6.9 2 2.8 6.2 2.8 11.3S6.9 20.6 12 20.6c6.9 0 9.1-4.9 9.1-7.4 0-.5 0-.9-.1-1.3H12z" />
            </svg>
            <span>{t("continueWithGoogle")}</span>
          </>
        )}
      </button>
    );
  }

  return (
    <div className="w-full min-h-[44px] relative" data-testid={testId}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl border border-[#8D99AE]/20 bg-white">
          <Loader2 className="w-4 h-4 animate-spin text-[#8D99AE]" />
        </div>
      )}
      <div ref={containerRef} className={loading ? "opacity-0" : "opacity-100"} />
    </div>
  );
}

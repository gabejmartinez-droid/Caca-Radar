import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { getGoogleClientId, isGoogleIdentitySupported, loadGoogleIdentityScript } from "../utils/googleIdentity";

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

  useEffect(() => {
    let cancelled = false;

    async function setupGoogleButton() {
      const clientId = getGoogleClientId();
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
  }, [context, onCredential, onError, t, text]);

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

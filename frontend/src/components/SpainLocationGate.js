import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, MapPin, ShieldAlert } from "lucide-react";
import { Button } from "./ui/button";
import { useLanguage } from "../contexts/LanguageContext";
import { formatTranslation } from "../utils/ranks";
import { isWithinSpain } from "../utils/spainLocation";

export default function SpainLocationGate({ children }) {
  const { t } = useLanguage();
  const [status, setStatus] = useState("checking");
  const [errorKey, setErrorKey] = useState("");

  const checkLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus("blocked");
      setErrorKey("appGateUi.noGeolocation");
      return;
    }

    setStatus("checking");
    setErrorKey("");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        if (isWithinSpain(latitude, longitude)) {
          setStatus("allowed");
          setErrorKey("");
        } else {
          setStatus("blocked");
          setErrorKey("appGateUi.outsideSpain");
        }
      },
      (error) => {
        setStatus("blocked");
        if (error?.code === 1) {
          setErrorKey("appGateUi.permissionDenied");
        } else if (error?.code === 2) {
          setErrorKey("appGateUi.unavailable");
        } else {
          setErrorKey("appGateUi.timeout");
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000,
      }
    );
  }, []);

  useEffect(() => {
    checkLocation();
  }, [checkLocation]);

  if (status === "allowed") {
    return children;
  }

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center px-5" data-testid="spain-location-gate">
      <div className="w-full max-w-md bg-white rounded-3xl border border-[#8D99AE]/10 shadow-sm p-6 text-center">
        {status === "checking" ? (
          <>
            <Loader2 className="w-10 h-10 text-[#FF6B6B] animate-spin mx-auto mb-4" />
            <h1 className="text-xl font-black text-[#2B2D42] mb-2">{t("appGateUi.checkingTitle")}</h1>
            <p className="text-sm text-[#5C677D]">{t("appGateUi.checkingBody")}</p>
          </>
        ) : (
          <>
            <div className="w-14 h-14 rounded-full bg-[#FF6B6B]/10 text-[#FF6B6B] flex items-center justify-center mx-auto mb-4">
              <ShieldAlert className="w-7 h-7" />
            </div>
            <h1 className="text-xl font-black text-[#2B2D42] mb-2">{t("appGateUi.blockedTitle")}</h1>
            <p className="text-sm text-[#5C677D] mb-4">
              {errorKey ? t(errorKey) : t("appGateUi.outsideSpain")}
            </p>
            <div className="rounded-2xl bg-[#F8F9FA] border border-[#8D99AE]/10 p-4 text-left mb-5">
              <div className="flex items-start gap-3">
                <MapPin className="w-4 h-4 text-[#FF6B6B] mt-0.5 shrink-0" />
                <p className="text-sm text-[#5C677D]">
                  {formatTranslation(t, "appGateUi.spainOnlyNotice", { country: "España" })}
                </p>
              </div>
            </div>
            <Button onClick={checkLocation} className="w-full bg-[#FF6B6B] hover:bg-[#FF5252] text-white rounded-xl py-5 font-bold mb-3">
              {t("appGateUi.retry")}
            </Button>
            <div className="flex items-center justify-center gap-4 text-xs text-[#8D99AE]">
              <Link to="/privacy" className="hover:text-[#2B2D42]">{t("legalUi.privacyPolicy")}</Link>
              <Link to="/terms" className="hover:text-[#2B2D42]">{t("legalUi.termsOfUse")}</Link>
              <Link to="/help" className="hover:text-[#2B2D42]">{t("legalUi.help")}</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

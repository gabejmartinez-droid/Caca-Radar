import { useState, useEffect } from "react";
import { useLanguage } from "../contexts/LanguageContext";

export default function PointsPopup({ points, breakdown, onDone }) {
  const [visible, setVisible] = useState(true);
  const { t } = useLanguage();

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      if (onDone) onDone();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onDone]);

  if (!visible || !points) return null;

  return (
    <div className="fixed inset-0 z-[3000] pointer-events-none flex items-center justify-center" data-testid="points-popup">
      <div className="bg-[#2B2D42] text-white rounded-2xl px-6 py-4 shadow-2xl animate-bounce-in text-center">
        <p className="text-3xl font-black mb-1" style={{ fontFamily: "Nunito, sans-serif" }}>+{points}</p>
        <p className="text-xs text-white/70">{t("pointsUi.pointsLabel")}</p>
        {breakdown && (
          <div className="mt-2 space-y-0.5">
            {Object.entries(breakdown).map(([key, val]) => (
              <p key={key} className="text-[10px] text-white/50">{key}: +{val}</p>
            ))}
          </div>
        )}
      </div>
      <style>{`
        @keyframes bounceIn {
          0% { transform: scale(0.3) translateY(40px); opacity: 0; }
          50% { transform: scale(1.1) translateY(-10px); opacity: 1; }
          70% { transform: scale(0.95) translateY(0); }
          100% { transform: scale(1) translateY(0); opacity: 1; }
        }
        .animate-bounce-in { animation: bounceIn 0.6s ease-out forwards; }
      `}</style>
    </div>
  );
}

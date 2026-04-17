import { useState, useEffect } from "react";
import { Flame } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

export default function StreakFlame() {
  const { user } = useAuth();
  const [show, setShow] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const streak = user?.streak_days || 0;

  useEffect(() => {
    if (streak >= 3 && !dismissed) {
      setShow(true);
      const timer = setTimeout(() => setShow(false), 8000);
      return () => clearTimeout(timer);
    }
  }, [streak, dismissed]);

  if (!show || streak < 3) return null;

  const flameSize = streak >= 30 ? "large" : streak >= 7 ? "medium" : "small";
  const flameColor = streak >= 30 ? "#FF3D00" : streak >= 7 ? "#FF6B6B" : "#FFA726";
  const flameGlow = streak >= 30 ? "0 0 24px #FF3D00" : streak >= 7 ? "0 0 16px #FF6B6B" : "0 0 10px #FFA726";

  const getMessage = () => {
    if (streak >= 30) return `${streak} dias seguidos! Leyenda!`;
    if (streak >= 7) return `${streak} dias de racha! Increible!`;
    return `${streak} dias seguidos!`;
  };

  return (
    <div
      className="absolute z-[1001] left-1/2 -translate-x-1/2 pointer-events-none"
      style={{ top: "calc(env(safe-area-inset-top, 0px) + 110px)" }}
      data-testid="streak-flame"
    >
      <div
        className="pointer-events-auto flex items-center gap-2 px-4 py-2.5 rounded-2xl cursor-pointer streak-flame-enter"
        style={{
          background: "rgba(43, 45, 66, 0.92)",
          backdropFilter: "blur(12px)",
          boxShadow: flameGlow,
        }}
        onClick={() => { setDismissed(true); setShow(false); }}
      >
        <div className={`streak-flame-icon streak-flame-${flameSize}`}>
          <Flame className="w-5 h-5" style={{ color: flameColor }} />
        </div>
        <div>
          <p className="text-white text-xs font-bold" style={{ fontFamily: "Nunito, sans-serif" }}>
            {getMessage()}
          </p>
          <p className="text-white/50 text-[10px]">Tu constancia marca la diferencia</p>
        </div>
        <div className="streak-counter" style={{ color: flameColor }}>
          <span className="text-lg font-black">{streak}</span>
        </div>
      </div>

      <style>{`
        @keyframes streakEnter {
          0% { transform: translateY(-20px) scale(0.8); opacity: 0; }
          40% { transform: translateY(4px) scale(1.02); opacity: 1; }
          60% { transform: translateY(-2px) scale(0.99); }
          100% { transform: translateY(0) scale(1); opacity: 1; }
        }
        @keyframes flamePulse {
          0%, 100% { transform: scale(1) rotate(0deg); }
          25% { transform: scale(1.15) rotate(-4deg); }
          50% { transform: scale(1.05) rotate(2deg); }
          75% { transform: scale(1.2) rotate(-2deg); }
        }
        @keyframes flameGlow {
          0%, 100% { filter: brightness(1); }
          50% { filter: brightness(1.4); }
        }
        .streak-flame-enter {
          animation: streakEnter 0.6s ease-out forwards;
        }
        .streak-flame-icon {
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .streak-flame-small svg {
          animation: flamePulse 1.5s ease-in-out infinite;
        }
        .streak-flame-medium svg {
          animation: flamePulse 1s ease-in-out infinite, flameGlow 2s ease-in-out infinite;
        }
        .streak-flame-large svg {
          animation: flamePulse 0.7s ease-in-out infinite, flameGlow 1.5s ease-in-out infinite;
          filter: drop-shadow(0 0 6px #FF3D00);
        }
        .streak-counter {
          font-family: 'Nunito', sans-serif;
          line-height: 1;
        }
      `}</style>
    </div>
  );
}

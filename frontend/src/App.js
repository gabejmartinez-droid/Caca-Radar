import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import UsernamePrompt from "./components/UsernamePrompt";
import NotificationChecker from "./components/NotificationChecker";
import MapPage from "./pages/MapPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import LeaderboardPage from "./pages/LeaderboardPage";
import RankingsPage from "./pages/RankingsPage";
import CityReportPage from "./pages/CityReportPage";
import SubscriptionPage from "./pages/SubscriptionPage";
import DashboardLogin from "./pages/DashboardLogin";
import Dashboard from "./pages/Dashboard";
import MunicipalityRegister from "./pages/MunicipalityRegister";
import ProfilePage from "./pages/ProfilePage";
import AnalyticsPage from "./pages/AnalyticsPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import ImpactPage from "./pages/ImpactPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import PrivacyPage from "./pages/PrivacyPage";
import HelpPage from "./pages/HelpPage";
import TermsPage from "./pages/TermsPage";
import DeleteAccountPage from "./pages/DeleteAccountPage";
import CookiesPage from "./pages/CookiesPage";
import CommunityGuidelinesPage from "./pages/CommunityGuidelinesPage";
import StatusPage from "./pages/StatusPage";
import { setupNativePushListeners } from "./utils/pushManager";
import { preparePlayIntegrity } from "./utils/playIntegrity";
import { isCapacitorNative } from "./tokenManager";
import "./App.css";

function UsernameGate({ children }) {
  const { user, checkAuth } = useAuth();
  if (user && user.needs_username) {
    return (
      <>
        {children}
        <UsernamePrompt onComplete={() => checkAuth()} />
      </>
    );
  }
  return children;
}

function App() {
  const [showNotificationChecker, setShowNotificationChecker] = useState(!isCapacitorNative());

  useEffect(() => {
    let cancelled = false;

    const startNativePushListeners = () => {
      if (cancelled) return;
      setupNativePushListeners();
    };

    if (isCapacitorNative()) {
      const idleHandle = window.requestIdleCallback?.(startNativePushListeners, { timeout: 1500 });
      const timeoutHandle = idleHandle ? null : window.setTimeout(startNativePushListeners, 600);

      return () => {
        cancelled = true;
        if (idleHandle) {
          window.cancelIdleCallback?.(idleHandle);
        }
        if (timeoutHandle) {
          window.clearTimeout(timeoutHandle);
        }
      };
    }

    startNativePushListeners();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isCapacitorNative()) return undefined;

    let cancelled = false;
    const warmIntegrity = () => {
      if (cancelled) return;
      preparePlayIntegrity().catch(() => {});
    };

    const idleId = window.requestIdleCallback?.(warmIntegrity, { timeout: 2500 });
    const timeoutId = idleId ? null : window.setTimeout(warmIntegrity, 1400);

    return () => {
      cancelled = true;
      if (idleId) window.cancelIdleCallback?.(idleId);
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, []);

  useEffect(() => {
    if (!isCapacitorNative()) return undefined;

    let timeoutId = null;
    let idleId = null;

    const enableChecker = () => {
      if (!cancelled) {
        setShowNotificationChecker(true);
      }
    };

    let cancelled = false;
    if (typeof window.requestIdleCallback === "function") {
      idleId = window.requestIdleCallback(enableChecker, { timeout: 2500 });
    } else {
      timeoutId = window.setTimeout(enableChecker, 1200);
    }

    return () => {
      cancelled = true;
      if (idleId) window.cancelIdleCallback?.(idleId);
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, []);

  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <UsernameGate>
            <Routes>
              <Route path="/" element={<MapPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/leaderboard" element={<LeaderboardPage />} />
              <Route path="/rankings" element={<RankingsPage />} />
              <Route path="/city-report" element={<CityReportPage />} />
              <Route path="/subscribe" element={<SubscriptionPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/dashboard/login" element={<DashboardLogin />} />
              <Route path="/dashboard/register" element={<MunicipalityRegister />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/dashboard/analytics" element={<AnalyticsPage />} />
              <Route path="/admin/login" element={<AdminLoginPage />} />
              <Route path="/admin" element={<AdminDashboardPage />} />
              <Route path="/impact" element={<ImpactPage />} />
              <Route path="/help" element={<HelpPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/delete-account" element={<DeleteAccountPage />} />
              <Route path="/cookies" element={<CookiesPage />} />
              <Route path="/status" element={<StatusPage />} />
              <Route path="/community" element={<CommunityGuidelinesPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
            </Routes>
          </UsernameGate>
          {showNotificationChecker && <NotificationChecker />}
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;

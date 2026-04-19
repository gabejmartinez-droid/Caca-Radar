import { useEffect } from "react";
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
import DeleteAccountPage from "./pages/DeleteAccountPage";
import { setupNativePushListeners } from "./utils/pushManager";
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
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/delete-account" element={<DeleteAccountPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
            </Routes>
          </UsernameGate>
          <NotificationChecker />
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;

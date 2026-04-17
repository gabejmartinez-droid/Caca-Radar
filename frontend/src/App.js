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
import GoogleCallbackPage from "./pages/GoogleCallbackPage";
import { setupNativePushListeners } from "./utils/pushManager";
import "./App.css";

// Initialize native push listeners for Capacitor
setupNativePushListeners();

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
              <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
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

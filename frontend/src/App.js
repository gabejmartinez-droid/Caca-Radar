import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import UsernamePrompt from "./components/UsernamePrompt";
import MapPage from "./pages/MapPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import LeaderboardPage from "./pages/LeaderboardPage";
import SubscriptionPage from "./pages/SubscriptionPage";
import DashboardLogin from "./pages/DashboardLogin";
import Dashboard from "./pages/Dashboard";
import MunicipalityRegister from "./pages/MunicipalityRegister";
import ProfilePage from "./pages/ProfilePage";
import AnalyticsPage from "./pages/AnalyticsPage";
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
              <Route path="/subscribe" element={<SubscriptionPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/dashboard/login" element={<DashboardLogin />} />
              <Route path="/dashboard/register" element={<MunicipalityRegister />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/dashboard/analytics" element={<AnalyticsPage />} />
            </Routes>
          </UsernameGate>
          <Toaster position="top-center" richColors />
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;

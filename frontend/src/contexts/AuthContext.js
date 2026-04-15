import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";

const AuthContext = createContext(null);

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(data);
      return data;
    } catch {
      setUser(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  const login = useCallback(async (email, password) => {
    const { data } = await axios.post(`${API}/auth/login`, { email, password }, { withCredentials: true });
    setUser(data);
    return data;
  }, []);

  const register = useCallback(async (email, password, username) => {
    const { data } = await axios.post(`${API}/auth/register`, { email, password, username }, { withCredentials: true });
    setUser(data);
    return data;
  }, []);

  const logout = useCallback(async () => {
    await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    setUser(false);
  }, []);

  const value = useMemo(() => ({ user, loading, login, register, logout, checkAuth }), [user, loading, login, register, logout, checkAuth]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

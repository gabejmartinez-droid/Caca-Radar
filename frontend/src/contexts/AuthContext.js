import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { API, APP_ENVIRONMENT, APP_VERSION } from "../config";
import { isCapacitorNative, setTokens, getAccessToken, getRefreshToken, clearTokens } from "../tokenManager";
import { disableGoogleAutoSelect } from "../utils/googleIdentity";
import { signOutGoogleNative } from "../utils/googleNative";
import { signInWithAppleNative } from "../utils/appleNative";
import { getCurrentPlatform } from "../versionInfo";

const AuthContext = createContext(null);

// Axios interceptor: attach Bearer token on native, handle auto-refresh on 401
axios.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers["X-App-Version"] = APP_VERSION;
  config.headers["X-App-Environment"] = APP_ENVIRONMENT;
  if (isCapacitorNative()) {
    const token = getAccessToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    config.headers["X-Platform"] = getCurrentPlatform();
    // Don't send cookies on native (they won't work due to proxy CORS)
    config.withCredentials = false;
  } else {
    config.headers["X-Platform"] = "web";
  }
  return config;
});

let isRefreshing = false;
let refreshQueue = [];

axios.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes("/auth/login") &&
      !original.url?.includes("/auth/register") &&
      !original.url?.includes("/auth/google/login") &&
      !original.url?.includes("/auth/google/link") &&
      !original.url?.includes("/auth/apple/login") &&
      !original.url?.includes("/auth/apple/link") &&
      !original.url?.includes("/auth/refresh")
    ) {
      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then(() => axios(original));
      }

      isRefreshing = true;
      try {
        const refreshPayload = isCapacitorNative()
          ? { refresh_token: getRefreshToken() }
          : {};
        const { data } = await axios.post(`${API}/auth/refresh`, refreshPayload, {
          withCredentials: !isCapacitorNative(),
        });
        if (data.access_token) {
          setTokens(data.access_token, getRefreshToken());
        }
        refreshQueue.forEach((p) => p.resolve());
        refreshQueue = [];
        return axios(original);
      } catch {
        refreshQueue.forEach((p) => p.reject(error));
        refreshQueue = [];
        clearTokens();
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/auth/me`, {
        withCredentials: !isCapacitorNative(),
      });
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
    const { data } = await axios.post(`${API}/auth/login`, { email, password }, {
      withCredentials: !isCapacitorNative(),
    });
    // Store tokens for native
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    setUser(data);
    return data;
  }, []);

  const register = useCallback(async (email, password, username) => {
    const { data } = await axios.post(`${API}/auth/register`, { email, password, username }, {
      withCredentials: !isCapacitorNative(),
    });
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    setUser(data);
    return data;
  }, []);

  const googleLogin = useCallback(async (credential) => {
    const { data } = await axios.post(
      `${API}/auth/google/login`,
      { credential },
      { withCredentials: !isCapacitorNative() },
    );
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    setUser(data);
    return data;
  }, []);

  const appleLogin = useCallback(async () => {
    const identity = await signInWithAppleNative();
    const { data } = await axios.post(
      `${API}/auth/apple/login`,
      {
        identity_token: identity.identityToken,
        authorization_code: identity.authorizationCode,
        email: identity.email,
        full_name: identity.fullName,
        given_name: identity.givenName,
        family_name: identity.familyName,
        user: identity.user,
      },
      { withCredentials: !isCapacitorNative() },
    );
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    setUser(data);
    return data;
  }, []);

  const linkGoogle = useCallback(async (credential) => {
    const { data } = await axios.post(
      `${API}/auth/google/link`,
      { credential },
      { withCredentials: !isCapacitorNative() },
    );
    await checkAuth();
    return data;
  }, [checkAuth]);

  const linkApple = useCallback(async () => {
    const identity = await signInWithAppleNative();
    const { data } = await axios.post(
      `${API}/auth/apple/link`,
      {
        identity_token: identity.identityToken,
        authorization_code: identity.authorizationCode,
        email: identity.email,
        full_name: identity.fullName,
        given_name: identity.givenName,
        family_name: identity.familyName,
        user: identity.user,
      },
      { withCredentials: !isCapacitorNative() },
    );
    await checkAuth();
    return data;
  }, [checkAuth]);

  const logout = useCallback(async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, {
        withCredentials: !isCapacitorNative(),
      });
    } catch { /* ignore */ }
    clearTokens();
    disableGoogleAutoSelect();
    await signOutGoogleNative();
    setUser(false);
  }, []);

  const deleteAccount = useCallback(async () => {
    const { data } = await axios.delete(`${API}/users/me`, {
      withCredentials: !isCapacitorNative(),
    });
    clearTokens();
    disableGoogleAutoSelect();
    await signOutGoogleNative();
    setUser(false);
    return data;
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, googleLogin, appleLogin, linkGoogle, linkApple, logout, deleteAccount, checkAuth }),
    [user, loading, login, register, googleLogin, appleLogin, linkGoogle, linkApple, logout, deleteAccount, checkAuth]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

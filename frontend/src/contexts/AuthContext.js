import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import axios from "axios";
import { API, APP_ENVIRONMENT, APP_VERSION } from "../config";
import { isCapacitorNative, initializeTokens, setTokens, getAccessToken, getRefreshToken, clearTokens } from "../tokenManager";
import { disableGoogleAutoSelect } from "../utils/googleIdentity";
import { signOutGoogleNative } from "../utils/googleNative";
import { signInWithAppleNative } from "../utils/appleNative";
import { isNativeAppleSupported, startAppleWebAuth } from "../utils/appleIdentity";
import { getCurrentPlatform } from "../versionInfo";
import { applyLanguagePreference } from "../utils/languagePreference";

const AuthContext = createContext(null);

// Axios interceptor: attach Bearer token on native, handle auto-refresh on 401
axios.interceptors.request.use(async (config) => {
  config.headers = config.headers || {};
  config.headers["X-App-Version"] = APP_VERSION;
  config.headers["X-App-Environment"] = APP_ENVIRONMENT;
  if (isCapacitorNative()) {
    await initializeTokens();
    const token = getAccessToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    config.headers["X-Platform"] = getCurrentPlatform();
    config.headers["X-Native-App"] = "1";
    // Default to token-based native requests, but allow explicit cookie-backed
    // bootstrap calls to opt in.
    if (typeof config.withCredentials === "undefined") {
      config.withCredentials = false;
    }
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
          await setTokens(data.access_token, getRefreshToken());
        }
        refreshQueue.forEach((p) => p.resolve());
        refreshQueue = [];
        return axios(original);
      } catch {
        refreshQueue.forEach((p) => p.reject(error));
        refreshQueue = [];
        await clearTokens();
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

  const ensureNativeSessionTokens = useCallback(async () => {
    if (!isCapacitorNative()) return;
    if (getAccessToken() && getRefreshToken()) return;
    const { data } = await axios.post(
      `${API}/auth/native/session-tokens`,
      {},
      {
        withCredentials: true,
        headers: {
          "X-Platform": getCurrentPlatform(),
          "X-Native-App": "1",
        },
      },
    );
    if (data?.access_token && data?.refresh_token) {
      await setTokens(data.access_token, data.refresh_token);
    }
  }, []);

  const syncUserLanguage = useCallback((data) => {
    if (data?.preferred_language) {
      applyLanguagePreference(data.preferred_language);
    }
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/auth/me`, {
        withCredentials: !isCapacitorNative(),
      });
      if (isCapacitorNative()) {
        await ensureNativeSessionTokens();
      }
      syncUserLanguage(data);
      setUser(data);
      return data;
    } catch {
      setUser(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, [ensureNativeSessionTokens, syncUserLanguage]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await initializeTokens();
      if (!cancelled) {
        await checkAuth();
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [checkAuth]);

  const login = useCallback(async (email, password) => {
    const { data } = await axios.post(`${API}/auth/login`, { email, password }, {
      withCredentials: !isCapacitorNative(),
    });
    // Store tokens for native
    if (data.access_token) {
      await setTokens(data.access_token, data.refresh_token);
    }
    syncUserLanguage(data);
    setUser(data);
    return data;
  }, [syncUserLanguage]);

  const register = useCallback(async (email, password, username) => {
    const { data } = await axios.post(`${API}/auth/register`, { email, password, username }, {
      withCredentials: !isCapacitorNative(),
    });
    if (data.access_token) {
      await setTokens(data.access_token, data.refresh_token);
    }
    syncUserLanguage(data);
    setUser(data);
    return data;
  }, [syncUserLanguage]);

  const googleLogin = useCallback(async (credential) => {
    const { data } = await axios.post(
      `${API}/auth/google/login`,
      { credential },
      { withCredentials: !isCapacitorNative() },
    );
    if (data.access_token) {
      await setTokens(data.access_token, data.refresh_token);
    }
    syncUserLanguage(data);
    setUser(data);
    return data;
  }, [syncUserLanguage]);

  const appleLogin = useCallback(async (nextPath = "/") => {
    if (!isNativeAppleSupported()) {
      startAppleWebAuth("login", nextPath);
      return { redirected: true };
    }
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
      await setTokens(data.access_token, data.refresh_token);
    }
    syncUserLanguage(data);
    setUser(data);
    return data;
  }, [syncUserLanguage]);

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
    if (!isNativeAppleSupported()) {
      startAppleWebAuth("link", "/profile");
      return { redirected: true };
    }
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
    await clearTokens();
    disableGoogleAutoSelect();
    await signOutGoogleNative();
    setUser(false);
  }, []);

  const deleteAccount = useCallback(async () => {
    const { data } = await axios.delete(`${API}/users/me`, {
      withCredentials: !isCapacitorNative(),
    });
    await clearTokens();
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

package com.jefe.cacaradar;

import android.content.Context;
import android.content.SharedPreferences;
import android.webkit.CookieManager;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

@CapacitorPlugin(name = "CompanionBridge")
public class CompanionBridgePlugin extends Plugin {
    public static final String PREFS_NAME = "caca_companion_bridge";
    private static final String SECURE_PREFS_NAME = "caca_secure_auth";
    public static final String ACCESS_TOKEN_KEY = "access_token";
    public static final String REFRESH_TOKEN_KEY = "refresh_token";
    public static final String API_BASE_URL_KEY = "api_base_url";
    public static final String PREFERRED_LANGUAGE_KEY = "preferred_language";

    static final class AuthStateSnapshot {
        final String accessToken;
        final String refreshToken;
        final String apiBaseUrl;

        AuthStateSnapshot(String accessToken, String refreshToken, String apiBaseUrl) {
            this.accessToken = accessToken;
            this.refreshToken = refreshToken;
            this.apiBaseUrl = apiBaseUrl;
        }
    }

    private SharedPreferences prefs() {
        Context context = getContext();
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    static SharedPreferences securePrefs(Context context) throws Exception {
        MasterKey masterKey = new MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build();
        return EncryptedSharedPreferences.create(
            context,
            SECURE_PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        );
    }

    static void persistAuthState(Context context, String accessToken, String refreshToken, boolean preserveStoredRefreshToken) throws Exception {
        SharedPreferences.Editor secureEditor = securePrefs(context)
            .edit()
            .putString(ACCESS_TOKEN_KEY, accessToken == null ? "" : accessToken);
        if (!preserveStoredRefreshToken || (refreshToken != null && !refreshToken.trim().isEmpty())) {
            secureEditor.putString(REFRESH_TOKEN_KEY, refreshToken == null ? "" : refreshToken);
        }
        secureEditor.apply();
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .remove(ACCESS_TOKEN_KEY)
            .remove(REFRESH_TOKEN_KEY)
            .apply();
    }

    static AuthStateSnapshot readAuthState(Context context) throws Exception {
        SharedPreferences secure = securePrefs(context);
        SharedPreferences general = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        String configuredBaseUrl = general.getString(API_BASE_URL_KEY, "https://cacaradar.es/api");
        String apiBaseUrl = configuredBaseUrl == null || configuredBaseUrl.trim().isEmpty()
            ? "https://cacaradar.es/api"
            : configuredBaseUrl.replaceAll("/+$", "");
        return new AuthStateSnapshot(
            secure.getString(ACCESS_TOKEN_KEY, ""),
            secure.getString(REFRESH_TOKEN_KEY, ""),
            apiBaseUrl
        );
    }

    static void clearStoredAuthState(Context context) throws Exception {
        securePrefs(context)
            .edit()
            .remove(ACCESS_TOKEN_KEY)
            .remove(REFRESH_TOKEN_KEY)
            .apply();
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .remove(ACCESS_TOKEN_KEY)
            .remove(REFRESH_TOKEN_KEY)
            .remove(API_BASE_URL_KEY)
            .apply();
    }

    @PluginMethod
    public void syncAuthState(PluginCall call) {
        String accessToken = call.getString("accessToken", "");
        String refreshToken = call.getString("refreshToken");
        String apiBaseUrl = call.getString("apiBaseUrl", "");
        boolean preserveStoredRefreshToken = call.getBoolean("preserveStoredRefreshToken", false);

        try {
            persistAuthState(getContext(), accessToken, refreshToken, preserveStoredRefreshToken);
            prefs()
                .edit()
                .putString(API_BASE_URL_KEY, apiBaseUrl)
                .apply();
            call.resolve(new JSObject());
        } catch (Exception exception) {
            call.reject("Failed to store auth state securely", exception);
        }
    }

    @PluginMethod
    public void getAuthState(PluginCall call) {
        try {
            AuthStateSnapshot authState = readAuthState(getContext());
            JSObject result = new JSObject();
            result.put("accessToken", authState.accessToken);
            result.put("apiBaseUrl", authState.apiBaseUrl);
            call.resolve(result);
        } catch (Exception exception) {
            call.reject("Failed to read auth state", exception);
        }
    }

    @PluginMethod
    public void bootstrapSessionFromCookies(PluginCall call) {
        getBridge().execute(() -> {
            try {
                String apiBaseUrl = normalizeApiBaseUrl(call.getString("apiBaseUrl", ""));
                String webOrigin = apiBaseUrl.endsWith("/api")
                    ? apiBaseUrl.substring(0, apiBaseUrl.length() - 4)
                    : apiBaseUrl;
                String cookieHeader = CookieManager.getInstance().getCookie(webOrigin);
                String cookieAccessToken = readCookieValue(cookieHeader, ACCESS_TOKEN_KEY);
                String cookieRefreshToken = readCookieValue(cookieHeader, REFRESH_TOKEN_KEY);
                AuthStateSnapshot existingState = readAuthState(getContext());
                String accessToken = cookieAccessToken == null || cookieAccessToken.trim().isEmpty()
                    ? existingState.accessToken
                    : cookieAccessToken;
                String refreshToken = cookieRefreshToken == null || cookieRefreshToken.trim().isEmpty()
                    ? existingState.refreshToken
                    : cookieRefreshToken;

                persistAuthState(
                    getContext(),
                    accessToken,
                    cookieRefreshToken == null || cookieRefreshToken.trim().isEmpty() ? null : refreshToken,
                    cookieRefreshToken == null || cookieRefreshToken.trim().isEmpty()
                );
                prefs()
                    .edit()
                    .putString(API_BASE_URL_KEY, apiBaseUrl)
                    .apply();

                JSObject result = new JSObject();
                result.put("accessToken", accessToken == null ? "" : accessToken);
                result.put("synced", refreshToken != null && !refreshToken.trim().isEmpty());
                call.resolve(result);
            } catch (Exception exception) {
                call.reject("Failed to bootstrap session from cookies", exception);
            }
        });
    }

    @PluginMethod
    public void refreshAccessToken(PluginCall call) {
        getBridge().execute(() -> {
            try {
                AuthStateSnapshot authState = readAuthState(getContext());
                if (authState.refreshToken == null || authState.refreshToken.trim().isEmpty()) {
                    call.reject("No refresh token available");
                    return;
                }

                String apiBaseUrl = normalizeApiBaseUrl(call.getString("apiBaseUrl", authState.apiBaseUrl));
                URL url = new URL(apiBaseUrl + "/auth/refresh");
                HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("POST");
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setRequestProperty("X-Native-App", "1");
                connection.setRequestProperty("X-Platform", "android");
                connection.setDoOutput(true);

                JSONObject body = new JSONObject();
                body.put("refresh_token", authState.refreshToken);
                try (OutputStream os = connection.getOutputStream()) {
                    os.write(body.toString().getBytes(StandardCharsets.UTF_8));
                }

                int status = connection.getResponseCode();
                if (status < 200 || status >= 300) {
                    call.reject("Refresh request failed");
                    return;
                }

                StringBuilder responseBuilder = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        responseBuilder.append(line);
                    }
                }
                JSONObject json = new JSONObject(responseBuilder.toString());
                String accessToken = json.optString("access_token", "");
                if (accessToken == null || accessToken.trim().isEmpty()) {
                    call.reject("No access token returned");
                    return;
                }

                persistAuthState(getContext(), accessToken, null, true);
                prefs()
                    .edit()
                    .putString(API_BASE_URL_KEY, apiBaseUrl)
                    .apply();

                JSObject result = new JSObject();
                result.put("accessToken", accessToken);
                call.resolve(result);
            } catch (Exception exception) {
                call.reject("Failed to refresh native access token", exception);
            }
        });
    }

    @PluginMethod
    public void syncPreferences(PluginCall call) {
        String preferredLanguage = call.getString("preferredLanguage", "");

        prefs()
            .edit()
            .putString(PREFERRED_LANGUAGE_KEY, preferredLanguage)
            .apply();

        call.resolve(new JSObject());
    }

    @PluginMethod
    public void clearAuthState(PluginCall call) {
        try {
            clearStoredAuthState(getContext());
            call.resolve(new JSObject());
        } catch (Exception exception) {
            call.reject("Failed to clear auth state", exception);
        }
    }

    private static String normalizeApiBaseUrl(String rawValue) {
        String trimmed = rawValue == null ? "" : rawValue.trim();
        if (trimmed.isEmpty()) {
            return "https://cacaradar.es/api";
        }
        String normalized = trimmed.replaceAll("/+$", "");
        if (normalized.endsWith("/api")) {
            return normalized;
        }
        return normalized + "/api";
    }

    private static String readCookieValue(String cookieHeader, String cookieName) {
        if (cookieHeader == null || cookieHeader.trim().isEmpty()) {
            return "";
        }
        String[] cookies = cookieHeader.split(";");
        for (String cookie : cookies) {
            String[] parts = cookie.trim().split("=", 2);
            if (parts.length == 2 && cookieName.equals(parts[0].trim())) {
                return parts[1].trim();
            }
        }
        return "";
    }
}

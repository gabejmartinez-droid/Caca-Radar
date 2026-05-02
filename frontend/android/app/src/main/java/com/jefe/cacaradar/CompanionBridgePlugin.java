package com.jefe.cacaradar;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

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

    static void persistAuthState(Context context, String accessToken, String refreshToken) throws Exception {
        securePrefs(context)
            .edit()
            .putString(ACCESS_TOKEN_KEY, accessToken == null ? "" : accessToken)
            .putString(REFRESH_TOKEN_KEY, refreshToken == null ? "" : refreshToken)
            .apply();
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
        String refreshToken = call.getString("refreshToken", "");
        String apiBaseUrl = call.getString("apiBaseUrl", "");

        try {
            persistAuthState(getContext(), accessToken, refreshToken);
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
            result.put("refreshToken", authState.refreshToken);
            result.put("apiBaseUrl", authState.apiBaseUrl);
            call.resolve(result);
        } catch (Exception exception) {
            call.reject("Failed to read auth state", exception);
        }
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
}

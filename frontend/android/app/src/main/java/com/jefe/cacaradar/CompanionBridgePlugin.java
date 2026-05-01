package com.jefe.cacaradar;

import android.content.Context;
import android.content.SharedPreferences;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "CompanionBridge")
public class CompanionBridgePlugin extends Plugin {
    public static final String PREFS_NAME = "caca_companion_bridge";
    public static final String ACCESS_TOKEN_KEY = "access_token";
    public static final String REFRESH_TOKEN_KEY = "refresh_token";
    public static final String API_BASE_URL_KEY = "api_base_url";

    private SharedPreferences prefs() {
        Context context = getContext();
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    @PluginMethod
    public void syncAuthState(PluginCall call) {
        String accessToken = call.getString("accessToken", "");
        String refreshToken = call.getString("refreshToken", "");
        String apiBaseUrl = call.getString("apiBaseUrl", "");

        prefs()
            .edit()
            .putString(ACCESS_TOKEN_KEY, accessToken)
            .putString(REFRESH_TOKEN_KEY, refreshToken)
            .putString(API_BASE_URL_KEY, apiBaseUrl)
            .apply();

        call.resolve(new JSObject());
    }

    @PluginMethod
    public void clearAuthState(PluginCall call) {
        prefs()
            .edit()
            .remove(ACCESS_TOKEN_KEY)
            .remove(REFRESH_TOKEN_KEY)
            .remove(API_BASE_URL_KEY)
            .apply();

        call.resolve(new JSObject());
    }
}

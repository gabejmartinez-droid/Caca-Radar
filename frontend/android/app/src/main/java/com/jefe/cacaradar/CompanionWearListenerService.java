package com.jefe.cacaradar;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.util.Log;

import com.google.android.gms.tasks.Tasks;
import com.google.android.gms.wearable.MessageClient;
import com.google.android.gms.wearable.MessageEvent;
import com.google.android.gms.wearable.Node;
import com.google.android.gms.wearable.Wearable;
import com.google.android.gms.wearable.WearableListenerService;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class CompanionWearListenerService extends WearableListenerService {
    private static final String TAG = "CompanionWear";
    private static final String QUICK_REPORT_PATH = "/quick-report";
    private static final String QUICK_REPORT_RESULT_PATH = "/quick-report/result";
    private static final String SETTINGS_REQUEST_PATH = "/companion-settings/request";
    private static final String SETTINGS_RESULT_PATH = "/companion-settings/result";

    @Override
    public void onMessageReceived(MessageEvent messageEvent) {
        if (SETTINGS_REQUEST_PATH.equals(messageEvent.getPath())) {
            try {
                sendSettings(messageEvent.getSourceNodeId());
            } catch (Exception exception) {
                Log.e(TAG, "Failed to sync watch settings", exception);
            }
            return;
        }

        if (!QUICK_REPORT_PATH.equals(messageEvent.getPath())) {
            super.onMessageReceived(messageEvent);
            return;
        }

        try {
            JSONObject payload = new JSONObject(new String(messageEvent.getData(), StandardCharsets.UTF_8));
            double latitude = payload.getDouble("latitude");
            double longitude = payload.getDouble("longitude");
            JSONObject result = performQuickReport(latitude, longitude);
            sendResult(messageEvent.getSourceNodeId(), result);
        } catch (Exception exception) {
            Log.e(TAG, "Failed to handle watch quick report", exception);
            try {
                JSONObject result = new JSONObject();
                result.put("ok", false);
                result.put("error", classifyErrorCode(exception));
                result.put("errorDetail", exception.getMessage() != null ? exception.getMessage() : "quick_report_failed");
                sendResult(messageEvent.getSourceNodeId(), result);
            } catch (Exception ignored) {
            }
        }
    }

    private JSONObject performQuickReport(double latitude, double longitude) throws Exception {
        SharedPreferences prefs = getSharedPreferences(CompanionBridgePlugin.PREFS_NAME, Context.MODE_PRIVATE);
        String accessToken = prefs.getString(CompanionBridgePlugin.ACCESS_TOKEN_KEY, "");
        String configuredBaseUrl = prefs.getString(CompanionBridgePlugin.API_BASE_URL_KEY, "https://cacaradar.es/api");
        String apiBaseUrl = configuredBaseUrl == null || configuredBaseUrl.trim().isEmpty()
            ? "https://cacaradar.es/api"
            : configuredBaseUrl.replaceAll("/+$", "");

        if (accessToken == null || accessToken.isEmpty()) {
            throw new IllegalStateException("missing_access_token");
        }

        URL url = new URL(apiBaseUrl + "/reports/quick");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + accessToken);
        connection.setDoOutput(true);
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(15000);

        JSONObject body = new JSONObject();
        body.put("latitude", latitude);
        body.put("longitude", longitude);
        body.put("source", "wear_os");

        try (OutputStream output = connection.getOutputStream()) {
            output.write(body.toString().getBytes(StandardCharsets.UTF_8));
        }

        int status = connection.getResponseCode();
        InputStream stream = status >= 200 && status < 300 ? connection.getInputStream() : connection.getErrorStream();
        String responseBody = readStream(stream);

        if (status < 200 || status >= 300) {
            JSONObject errorBody = responseBody != null && !responseBody.isEmpty() ? new JSONObject(responseBody) : new JSONObject();
            throw new IllegalStateException(errorBody.optString("detail", "quick_report_failed"));
        }

        JSONObject response = responseBody != null && !responseBody.isEmpty() ? new JSONObject(responseBody) : new JSONObject();
        JSONObject result = new JSONObject();
        result.put("ok", true);
        result.put("reportId", response.optString("id", ""));
        result.put("municipality", response.optString("municipality", ""));
        result.put("convertedToConfirmation", response.optBoolean("converted_to_confirmation", false));
        return result;
    }

    private void sendSettings(String nodeId) throws Exception {
        SharedPreferences prefs = getSharedPreferences(CompanionBridgePlugin.PREFS_NAME, Context.MODE_PRIVATE);
        String accessToken = prefs.getString(CompanionBridgePlugin.ACCESS_TOKEN_KEY, "");
        JSONObject result = new JSONObject();
        result.put("preferredLanguage", prefs.getString(CompanionBridgePlugin.PREFERRED_LANGUAGE_KEY, "es"));
        result.put("authenticated", accessToken != null && !accessToken.isEmpty());
        MessageClient client = Wearable.getMessageClient(this);
        Tasks.await(client.sendMessage(nodeId, SETTINGS_RESULT_PATH, result.toString().getBytes(StandardCharsets.UTF_8)), 15, TimeUnit.SECONDS);
    }

    private void sendResult(String nodeId, JSONObject result) throws Exception {
        MessageClient client = Wearable.getMessageClient(this);
        Tasks.await(client.sendMessage(nodeId, QUICK_REPORT_RESULT_PATH, result.toString().getBytes(StandardCharsets.UTF_8)), 15, TimeUnit.SECONDS);
    }

    private String readStream(InputStream stream) throws Exception {
        if (stream == null) return "";
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
            return builder.toString();
        }
    }

    private String classifyErrorCode(Exception exception) {
        String message = exception.getMessage() != null ? exception.getMessage() : "";
        if ("missing_access_token".equals(message)) return "missing_access_token";
        if ("invalid_api_url".equals(message)) return "invalid_api_url";
        if (message.contains("30 segundos")) return "report_cooldown";
        if (message.contains("restringida")) return "restricted_account";
        return "quick_report_failed";
    }
}

package com.jefe.cacaradar;

import android.util.Log;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.play.core.integrity.IntegrityManagerFactory;
import com.google.android.play.core.integrity.StandardIntegrityManager;

@CapacitorPlugin(name = "PlayIntegrity")
public class PlayIntegrityPlugin extends Plugin {
    private static final String TAG = "PlayIntegrityPlugin";
    private StandardIntegrityManager standardIntegrityManager;
    private StandardIntegrityManager.StandardIntegrityTokenProvider tokenProvider;
    private Long preparedProjectNumber;

    private StandardIntegrityManager getManager() {
        if (standardIntegrityManager == null) {
            standardIntegrityManager = IntegrityManagerFactory.createStandard(getContext());
        }
        return standardIntegrityManager;
    }

    @PluginMethod
    public void prepare(PluginCall call) {
        Long cloudProjectNumber = call.getLong("cloudProjectNumber");
        if (cloudProjectNumber == null || cloudProjectNumber <= 0) {
            call.reject("Missing valid cloudProjectNumber");
            return;
        }

        getManager()
            .prepareIntegrityToken(
                StandardIntegrityManager.PrepareIntegrityTokenRequest.builder()
                    .setCloudProjectNumber(cloudProjectNumber)
                    .build()
            )
            .addOnSuccessListener(provider -> {
                tokenProvider = provider;
                preparedProjectNumber = cloudProjectNumber;
                JSObject result = new JSObject();
                result.put("prepared", true);
                result.put("cloudProjectNumber", cloudProjectNumber);
                call.resolve(result);
            })
            .addOnFailureListener(exception -> {
                Log.e(TAG, "prepareIntegrityToken failed", exception);
                call.reject("Failed to prepare Play Integrity token provider", exception);
            });
    }

    @PluginMethod
    public void requestToken(PluginCall call) {
        String requestHash = call.getString("requestHash");
        if (requestHash == null || requestHash.trim().isEmpty()) {
            call.reject("Missing requestHash");
            return;
        }
        if (tokenProvider == null) {
            call.reject("Play Integrity token provider is not prepared");
            return;
        }

        tokenProvider
            .request(
                StandardIntegrityManager.StandardIntegrityTokenRequest.builder()
                    .setRequestHash(requestHash)
                    .build()
            )
            .addOnSuccessListener(response -> {
                JSObject result = new JSObject();
                result.put("token", response.token());
                result.put("requestHash", requestHash);
                if (preparedProjectNumber != null) {
                    result.put("cloudProjectNumber", preparedProjectNumber);
                }
                call.resolve(result);
            })
            .addOnFailureListener(exception -> {
                Log.e(TAG, "requestIntegrityToken failed", exception);
                call.reject("Failed to request Play Integrity token", exception);
            });
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject result = new JSObject();
        result.put("prepared", tokenProvider != null);
        if (preparedProjectNumber != null) {
            result.put("cloudProjectNumber", preparedProjectNumber);
        }
        call.resolve(result);
    }
}

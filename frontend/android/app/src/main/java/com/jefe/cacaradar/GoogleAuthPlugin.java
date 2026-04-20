package com.jefe.cacaradar;

import android.app.Activity;
import android.content.Intent;
import android.util.Log;

import androidx.activity.result.ActivityResult;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.gms.auth.api.signin.GoogleSignIn;
import com.google.android.gms.auth.api.signin.GoogleSignInAccount;
import com.google.android.gms.auth.api.signin.GoogleSignInClient;
import com.google.android.gms.auth.api.signin.GoogleSignInOptions;
import com.google.android.gms.common.api.ApiException;

@CapacitorPlugin(name = "GoogleAuth")
public class GoogleAuthPlugin extends Plugin {
    private static final String TAG = "GoogleAuthPlugin";
    private GoogleSignInClient googleSignInClient;

    private GoogleSignInClient getClient(String serverClientId) {
        GoogleSignInOptions options = new GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestEmail()
            .requestIdToken(serverClientId)
            .build();
        googleSignInClient = GoogleSignIn.getClient(getActivity(), options);
        return googleSignInClient;
    }

    @PluginMethod
    public void signIn(PluginCall call) {
        String serverClientId = call.getString("serverClientId");
        if (serverClientId == null || serverClientId.trim().isEmpty()) {
            call.reject("Missing serverClientId");
            return;
        }

        try {
            Intent signInIntent = getClient(serverClientId.trim()).getSignInIntent();
            startActivityForResult(call, signInIntent, "handleSignInResult");
        } catch (Exception exception) {
            Log.e(TAG, "Unable to start Google sign-in", exception);
            call.reject("Failed to start Google sign-in", exception);
        }
    }

    @ActivityCallback
    private void handleSignInResult(PluginCall call, ActivityResult result) {
        if (call == null) {
            return;
        }

        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) {
            call.reject("Google sign-in was cancelled");
            return;
        }

        try {
            GoogleSignInAccount account = GoogleSignIn.getSignedInAccountFromIntent(result.getData())
                .getResult(ApiException.class);
            if (account == null || account.getIdToken() == null || account.getIdToken().trim().isEmpty()) {
                call.reject("Google sign-in did not return an ID token");
                return;
            }

            JSObject response = new JSObject();
            response.put("idToken", account.getIdToken());
            response.put("email", account.getEmail());
            response.put("displayName", account.getDisplayName());
            response.put("photoUrl", account.getPhotoUrl() != null ? account.getPhotoUrl().toString() : null);
            call.resolve(response);
        } catch (ApiException exception) {
            Log.e(TAG, "Google sign-in failed", exception);
            call.reject("Google sign-in failed", exception);
        } catch (Exception exception) {
            Log.e(TAG, "Unexpected Google sign-in error", exception);
            call.reject("Unexpected Google sign-in error", exception);
        }
    }

    @PluginMethod
    public void signOut(PluginCall call) {
        if (googleSignInClient == null) {
            call.resolve();
            return;
        }

        googleSignInClient
            .signOut()
            .addOnSuccessListener(unused -> call.resolve())
            .addOnFailureListener(exception -> {
                Log.w(TAG, "Google sign-out failed", exception);
                call.resolve();
            });
    }
}

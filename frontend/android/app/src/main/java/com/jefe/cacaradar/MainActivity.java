package com.jefe.cacaradar;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(PlayIntegrityPlugin.class);
        registerPlugin(GoogleAuthPlugin.class);
        super.onCreate(savedInstanceState);
    }
}

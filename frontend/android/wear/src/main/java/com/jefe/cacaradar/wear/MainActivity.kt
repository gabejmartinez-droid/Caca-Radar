package com.jefe.cacaradar.wear

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.wear.compose.material.Button
import androidx.wear.compose.material.MaterialTheme
import androidx.wear.compose.material.Text
import com.google.android.gms.location.LocationServices
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.MessageClient
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.nio.charset.StandardCharsets
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity(), MessageClient.OnMessageReceivedListener {
    private val permissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) {}
    private var statusUpdater: ((String) -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Wearable.getMessageClient(this).addListener(this)

        setContent {
            var status by remember { mutableStateOf("Pulsa para enviar un aviso sin foto.") }
            statusUpdater = { status = it }
            MaterialTheme {
                Column(
                    modifier = Modifier.fillMaxSize().padding(12.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text("Caca Radar", textAlign = TextAlign.Center)
                    Text(status, textAlign = TextAlign.Center, modifier = Modifier.padding(vertical = 8.dp))
                    Button(onClick = { submitQuickReport() }) {
                        Text("Reportar ahora")
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        Wearable.getMessageClient(this).removeListener(this)
        super.onDestroy()
    }

    override fun onMessageReceived(messageEvent: MessageEvent) {
        if (messageEvent.path != "/quick-report/result") return
        val json = JSONObject(String(messageEvent.data, StandardCharsets.UTF_8))
        val ok = json.optBoolean("ok", false)
        val municipality = json.optString("municipality", "")
        val converted = json.optBoolean("convertedToConfirmation", false)
        val error = json.optString("error", "No se pudo enviar el aviso")
        runOnUiThread {
            statusUpdater?.invoke(
                if (ok) {
                    if (converted) "Aviso confirmado en $municipality"
                    else "Aviso enviado en $municipality"
                } else {
                    error
                }
            )
        }
    }

    private fun submitQuickReport() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            permissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
            return
        }

        lifecycleScope.launch {
            statusUpdater?.invoke("Buscando ubicación…")
            try {
                val location = getCurrentLocation() ?: run {
                    statusUpdater?.invoke("No se pudo obtener la ubicación")
                    return@launch
                }
                statusUpdater?.invoke("Enviando al teléfono…")
                val nodes = Tasks.await(Wearable.getNodeClient(this@MainActivity).connectedNodes, 10, TimeUnit.SECONDS)
                val payload = JSONObject()
                    .put("latitude", location.latitude)
                    .put("longitude", location.longitude)
                    .toString()
                    .toByteArray(StandardCharsets.UTF_8)
                nodes.forEach { node ->
                    Tasks.await(Wearable.getMessageClient(this@MainActivity).sendMessage(node.id, "/quick-report", payload), 10, TimeUnit.SECONDS)
                }
                statusUpdater?.invoke("Esperando confirmación…")
            } catch (exception: Exception) {
                statusUpdater?.invoke(exception.message ?: "Error al enviar el aviso")
            }
        }
    }

    @SuppressLint("MissingPermission")
    private suspend fun getCurrentLocation() =
        Tasks.await(LocationServices.getFusedLocationProviderClient(this).lastLocation, 10, TimeUnit.SECONDS)
}

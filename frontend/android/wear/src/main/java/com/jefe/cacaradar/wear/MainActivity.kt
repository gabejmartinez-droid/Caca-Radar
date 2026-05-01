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
import java.util.Locale
import java.util.concurrent.TimeUnit

private const val QUICK_REPORT_PATH = "/quick-report"
private const val QUICK_REPORT_RESULT_PATH = "/quick-report/result"
private const val SETTINGS_REQUEST_PATH = "/companion-settings/request"
private const val SETTINGS_RESULT_PATH = "/companion-settings/result"

private enum class WatchStringKey {
    APP_TITLE,
    TAP_TO_REPORT,
    REPORT_NOW,
    SENDING,
    PHONE_UNAVAILABLE,
    REPORT_SENT,
    REPORT_CONFIRMED,
    LOCATION_PERMISSION_DENIED,
    LOCATION_UNAVAILABLE,
    WAITING_FOR_LOCATION,
    WAITING_FOR_PHONE,
    MISSING_ACCESS_TOKEN,
    REPORT_COOLDOWN,
    RESTRICTED_ACCOUNT,
    QUICK_REPORT_FAILED,
}

private data class WearStrings(val values: Map<WatchStringKey, String>) {
    fun text(key: WatchStringKey): String = values[key] ?: wearStrings("es").values[key].orEmpty()
}

private fun wearStrings(code: String): WearStrings = when (code) {
    "en" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Tap to report poop here.",
        WatchStringKey.REPORT_NOW to "Report now",
        WatchStringKey.SENDING to "Sending...",
        WatchStringKey.PHONE_UNAVAILABLE to "Open the phone app or bring it closer to the watch.",
        WatchStringKey.REPORT_SENT to "Report sent in %s.",
        WatchStringKey.REPORT_CONFIRMED to "Existing report confirmed in %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Allow location access on the watch to send reports.",
        WatchStringKey.LOCATION_UNAVAILABLE to "We couldn't get your location.",
        WatchStringKey.WAITING_FOR_LOCATION to "Getting your location…",
        WatchStringKey.WAITING_FOR_PHONE to "Waiting for the phone…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Open Caca Radar on the phone and sign in again.",
        WatchStringKey.REPORT_COOLDOWN to "Please wait 30 seconds between reports.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Your account is temporarily restricted.",
        WatchStringKey.QUICK_REPORT_FAILED to "The report couldn't be sent.",
    ))
    "de" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Tippe hier, um Hundekot zu melden.",
        WatchStringKey.REPORT_NOW to "Jetzt melden",
        WatchStringKey.SENDING to "Wird gesendet...",
        WatchStringKey.PHONE_UNAVAILABLE to "Öffne die Handy-App oder bringe das Handy näher an die Uhr.",
        WatchStringKey.REPORT_SENT to "Meldung in %s gesendet.",
        WatchStringKey.REPORT_CONFIRMED to "Bestehende Meldung in %s bestätigt.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Erlaube Standortzugriff auf der Uhr, um Meldungen zu senden.",
        WatchStringKey.LOCATION_UNAVAILABLE to "Der Standort konnte nicht ermittelt werden.",
        WatchStringKey.WAITING_FOR_LOCATION to "Standort wird ermittelt…",
        WatchStringKey.WAITING_FOR_PHONE to "Warte auf das Handy…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Öffne Caca Radar auf dem Handy und melde dich erneut an.",
        WatchStringKey.REPORT_COOLDOWN to "Bitte warte 30 Sekunden zwischen Meldungen.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Dein Konto ist vorübergehend eingeschränkt.",
        WatchStringKey.QUICK_REPORT_FAILED to "Die Meldung konnte nicht gesendet werden.",
    ))
    "nl" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Tik om hier hondenpoep te melden.",
        WatchStringKey.REPORT_NOW to "Nu melden",
        WatchStringKey.SENDING to "Verzenden...",
        WatchStringKey.PHONE_UNAVAILABLE to "Open de telefoonapp of houd de telefoon dichter bij het horloge.",
        WatchStringKey.REPORT_SENT to "Melding verzonden in %s.",
        WatchStringKey.REPORT_CONFIRMED to "Bestaande melding bevestigd in %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Geef locatie-toegang op het horloge om meldingen te versturen.",
        WatchStringKey.LOCATION_UNAVAILABLE to "We konden je locatie niet ophalen.",
        WatchStringKey.WAITING_FOR_LOCATION to "Locatie ophalen…",
        WatchStringKey.WAITING_FOR_PHONE to "Wachten op de telefoon…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Open Caca Radar op de telefoon en log opnieuw in.",
        WatchStringKey.REPORT_COOLDOWN to "Wacht 30 seconden tussen meldingen.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Je account is tijdelijk beperkt.",
        WatchStringKey.QUICK_REPORT_FAILED to "De melding kon niet worden verzonden.",
    ))
    "pl" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Stuknij, aby zgłosić tu kupę.",
        WatchStringKey.REPORT_NOW to "Zgłoś teraz",
        WatchStringKey.SENDING to "Wysyłanie...",
        WatchStringKey.PHONE_UNAVAILABLE to "Otwórz aplikację w telefonie lub zbliż telefon do zegarka.",
        WatchStringKey.REPORT_SENT to "Zgłoszenie wysłane w %s.",
        WatchStringKey.REPORT_CONFIRMED to "Istniejące zgłoszenie potwierdzone w %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Zezwól zegarkowi na dostęp do lokalizacji, aby wysyłać zgłoszenia.",
        WatchStringKey.LOCATION_UNAVAILABLE to "Nie udało się pobrać lokalizacji.",
        WatchStringKey.WAITING_FOR_LOCATION to "Pobieranie lokalizacji…",
        WatchStringKey.WAITING_FOR_PHONE to "Oczekiwanie na telefon…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Otwórz Caca Radar w telefonie i zaloguj się ponownie.",
        WatchStringKey.REPORT_COOLDOWN to "Odczekaj 30 sekund między zgłoszeniami.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Twoje konto jest tymczasowo ograniczone.",
        WatchStringKey.QUICK_REPORT_FAILED to "Nie udało się wysłać zgłoszenia.",
    ))
    "uk" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Натисніть, щоб повідомити про собачі екскременти тут.",
        WatchStringKey.REPORT_NOW to "Повідомити",
        WatchStringKey.SENDING to "Надсилання...",
        WatchStringKey.PHONE_UNAVAILABLE to "Відкрийте застосунок на телефоні або піднесіть його ближче до годинника.",
        WatchStringKey.REPORT_SENT to "Звіт надіслано в %s.",
        WatchStringKey.REPORT_CONFIRMED to "Наявний звіт підтверджено в %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Дозвольте доступ до геопозиції на годиннику, щоб надсилати звіти.",
        WatchStringKey.LOCATION_UNAVAILABLE to "Не вдалося отримати вашу геопозицію.",
        WatchStringKey.WAITING_FOR_LOCATION to "Отримуємо геопозицію…",
        WatchStringKey.WAITING_FOR_PHONE to "Чекаємо на телефон…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Відкрийте Caca Radar на телефоні та увійдіть ще раз.",
        WatchStringKey.REPORT_COOLDOWN to "Зачекайте 30 секунд між звітами.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Ваш акаунт тимчасово обмежено.",
        WatchStringKey.QUICK_REPORT_FAILED to "Не вдалося надіслати звіт.",
    ))
    "ru" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Нажмите, чтобы сообщить о собачьих отходах здесь.",
        WatchStringKey.REPORT_NOW to "Сообщить",
        WatchStringKey.SENDING to "Отправка...",
        WatchStringKey.PHONE_UNAVAILABLE to "Откройте приложение на телефоне или поднесите его ближе к часам.",
        WatchStringKey.REPORT_SENT to "Сообщение отправлено в %s.",
        WatchStringKey.REPORT_CONFIRMED to "Существующее сообщение подтверждено в %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Разрешите доступ к геопозиции на часах, чтобы отправлять сообщения.",
        WatchStringKey.LOCATION_UNAVAILABLE to "Не удалось получить вашу геопозицию.",
        WatchStringKey.WAITING_FOR_LOCATION to "Получаем геопозицию…",
        WatchStringKey.WAITING_FOR_PHONE to "Ожидание телефона…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Откройте Caca Radar на телефоне и войдите снова.",
        WatchStringKey.REPORT_COOLDOWN to "Подождите 30 секунд между сообщениями.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Ваш аккаунт временно ограничен.",
        WatchStringKey.QUICK_REPORT_FAILED to "Не удалось отправить сообщение.",
    ))
    "ca" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Toca per informar de caca de gos aquí.",
        WatchStringKey.REPORT_NOW to "Informa ara",
        WatchStringKey.SENDING to "Enviant...",
        WatchStringKey.PHONE_UNAVAILABLE to "Obre l'app del telèfon o acosta'l més al rellotge.",
        WatchStringKey.REPORT_SENT to "Avís enviat a %s.",
        WatchStringKey.REPORT_CONFIRMED to "Avís existent confirmat a %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Permet l'accés a la ubicació al rellotge per enviar avisos.",
        WatchStringKey.LOCATION_UNAVAILABLE to "No hem pogut obtenir la teva ubicació.",
        WatchStringKey.WAITING_FOR_LOCATION to "Obtenint la ubicació…",
        WatchStringKey.WAITING_FOR_PHONE to "Esperant el telèfon…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Obre Caca Radar al telèfon i torna a iniciar sessió.",
        WatchStringKey.REPORT_COOLDOWN to "Espera 30 segons entre avisos.",
        WatchStringKey.RESTRICTED_ACCOUNT to "El teu compte està restringit temporalment.",
        WatchStringKey.QUICK_REPORT_FAILED to "No s'ha pogut enviar l'avís.",
    ))
    "val" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Toca per a informar de caca de gos ací.",
        WatchStringKey.REPORT_NOW to "Informa ara",
        WatchStringKey.SENDING to "Enviant...",
        WatchStringKey.PHONE_UNAVAILABLE to "Obri l'app del telèfon o acosta'l més al rellotge.",
        WatchStringKey.REPORT_SENT to "Avís enviat a %s.",
        WatchStringKey.REPORT_CONFIRMED to "Avís existent confirmat a %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Permet l'accés a la ubicació al rellotge per a enviar avisos.",
        WatchStringKey.LOCATION_UNAVAILABLE to "No hem pogut obtindre la teua ubicació.",
        WatchStringKey.WAITING_FOR_LOCATION to "Obtenint la ubicació…",
        WatchStringKey.WAITING_FOR_PHONE to "Esperant el telèfon…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Obri Caca Radar al telèfon i torna a iniciar sessió.",
        WatchStringKey.REPORT_COOLDOWN to "Espera 30 segons entre avisos.",
        WatchStringKey.RESTRICTED_ACCOUNT to "El teu compte està restringit temporalment.",
        WatchStringKey.QUICK_REPORT_FAILED to "No s'ha pogut enviar l'avís.",
    ))
    "eu" -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Sakatu hemen txakur-kakaren abisua bidaltzeko.",
        WatchStringKey.REPORT_NOW to "Jakinarazi orain",
        WatchStringKey.SENDING to "Bidaltzen...",
        WatchStringKey.PHONE_UNAVAILABLE to "Ireki telefonoko aplikazioa edo hurbildu telefonoa erlojuara.",
        WatchStringKey.REPORT_SENT to "Abisua %s herrian bidali da.",
        WatchStringKey.REPORT_CONFIRMED to "Lehendik zegoen abisua %s herrian baieztatu da.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Baimendu kokapena erlojuan abisuak bidaltzeko.",
        WatchStringKey.LOCATION_UNAVAILABLE to "Ezin izan dugu zure kokapena lortu.",
        WatchStringKey.WAITING_FOR_LOCATION to "Kokapena lortzen…",
        WatchStringKey.WAITING_FOR_PHONE to "Telefonoaren zain…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Ireki Caca Radar telefonoan eta hasi saioa berriro.",
        WatchStringKey.REPORT_COOLDOWN to "Itxaron 30 segundo abisuen artean.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Zure kontua aldi baterako mugatuta dago.",
        WatchStringKey.QUICK_REPORT_FAILED to "Ezin izan da abisua bidali.",
    ))
    else -> WearStrings(mapOf(
        WatchStringKey.APP_TITLE to "Caca Radar",
        WatchStringKey.TAP_TO_REPORT to "Pulsa para enviar un aviso sin foto.",
        WatchStringKey.REPORT_NOW to "Reportar ahora",
        WatchStringKey.SENDING to "Enviando...",
        WatchStringKey.PHONE_UNAVAILABLE to "Abre la app del teléfono o acércalo al reloj.",
        WatchStringKey.REPORT_SENT to "Aviso enviado en %s.",
        WatchStringKey.REPORT_CONFIRMED to "Se confirmó un aviso existente en %s.",
        WatchStringKey.LOCATION_PERMISSION_DENIED to "Permite la ubicación en el reloj para enviar avisos.",
        WatchStringKey.LOCATION_UNAVAILABLE to "No pudimos obtener tu ubicación.",
        WatchStringKey.WAITING_FOR_LOCATION to "Buscando tu ubicación…",
        WatchStringKey.WAITING_FOR_PHONE to "Esperando el teléfono…",
        WatchStringKey.MISSING_ACCESS_TOKEN to "Abre Caca Radar en el teléfono e inicia sesión de nuevo.",
        WatchStringKey.REPORT_COOLDOWN to "Espera 30 segundos entre reportes.",
        WatchStringKey.RESTRICTED_ACCOUNT to "Tu cuenta está restringida temporalmente.",
        WatchStringKey.QUICK_REPORT_FAILED to "No se pudo enviar el aviso.",
    ))
}

class MainActivity : ComponentActivity(), MessageClient.OnMessageReceivedListener {
    private var preferredLanguage = Locale.getDefault().language.ifEmpty { "es" }
    private var languageUpdater: ((String) -> Unit)? = null
    private val permissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            submitQuickReport()
        } else {
            statusUpdater?.invoke(strings().text(WatchStringKey.LOCATION_PERMISSION_DENIED))
        }
    }
    private var statusUpdater: ((String) -> Unit)? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Wearable.getMessageClient(this).addListener(this)

        setContent {
            var uiLanguage by remember { mutableStateOf(preferredLanguage) }
            var status by remember { mutableStateOf(wearStrings(uiLanguage).text(WatchStringKey.TAP_TO_REPORT)) }
            statusUpdater = { status = it }
            languageUpdater = { nextLanguage ->
                uiLanguage = nextLanguage
                status = wearStrings(nextLanguage).text(WatchStringKey.TAP_TO_REPORT)
            }
            MaterialTheme {
                Column(
                    modifier = Modifier.fillMaxSize().padding(12.dp),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(wearStrings(uiLanguage).text(WatchStringKey.APP_TITLE), textAlign = TextAlign.Center)
                    Text(status, textAlign = TextAlign.Center, modifier = Modifier.padding(vertical = 8.dp))
                    Button(onClick = { submitQuickReport() }) {
                        Text(wearStrings(uiLanguage).text(WatchStringKey.REPORT_NOW))
                    }
                }
            }
        }

        requestPhoneSettings()
    }

    override fun onDestroy() {
        Wearable.getMessageClient(this).removeListener(this)
        super.onDestroy()
    }

    override fun onMessageReceived(messageEvent: MessageEvent) {
        when (messageEvent.path) {
            QUICK_REPORT_RESULT_PATH -> {
                val json = JSONObject(String(messageEvent.data, StandardCharsets.UTF_8))
                val ok = json.optBoolean("ok", false)
                val municipality = json.optString("municipality", "")
                val converted = json.optBoolean("convertedToConfirmation", false)
                val errorCode = json.optString("error", "quick_report_failed")
                val errorDetail = json.optString("errorDetail", errorCode)
                runOnUiThread {
                    statusUpdater?.invoke(
                        if (ok) {
                            if (converted) strings().text(WatchStringKey.REPORT_CONFIRMED).format(municipality)
                            else strings().text(WatchStringKey.REPORT_SENT).format(municipality)
                        } else {
                            localizeError(errorCode, errorDetail)
                        }
                    )
                }
            }
            SETTINGS_RESULT_PATH -> {
                val json = JSONObject(String(messageEvent.data, StandardCharsets.UTF_8))
                val nextLanguage = json.optString("preferredLanguage", preferredLanguage).ifBlank { preferredLanguage }
                preferredLanguage = nextLanguage
                runOnUiThread {
                    languageUpdater?.invoke(nextLanguage)
                }
            }
        }
    }

    private fun submitQuickReport() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            permissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
            return
        }

        lifecycleScope.launch {
            statusUpdater?.invoke(strings().text(WatchStringKey.WAITING_FOR_LOCATION))
            try {
                val location = getCurrentLocation() ?: run {
                    statusUpdater?.invoke(strings().text(WatchStringKey.LOCATION_UNAVAILABLE))
                    return@launch
                }
                statusUpdater?.invoke(strings().text(WatchStringKey.WAITING_FOR_PHONE))
                val nodes = Tasks.await(Wearable.getNodeClient(this@MainActivity).connectedNodes, 10, TimeUnit.SECONDS)
                if (nodes.isEmpty()) {
                    statusUpdater?.invoke(strings().text(WatchStringKey.PHONE_UNAVAILABLE))
                    return@launch
                }
                val payload = JSONObject()
                    .put("latitude", location.latitude)
                    .put("longitude", location.longitude)
                    .toString()
                    .toByteArray(StandardCharsets.UTF_8)
                nodes.forEach { node ->
                    Tasks.await(Wearable.getMessageClient(this@MainActivity).sendMessage(node.id, QUICK_REPORT_PATH, payload), 10, TimeUnit.SECONDS)
                }
                statusUpdater?.invoke(strings().text(WatchStringKey.SENDING))
            } catch (exception: Exception) {
                statusUpdater?.invoke(localizeError("quick_report_failed", exception.message))
            }
        }
    }

    private fun requestPhoneSettings() {
        lifecycleScope.launch {
            try {
                val nodes = Tasks.await(Wearable.getNodeClient(this@MainActivity).connectedNodes, 10, TimeUnit.SECONDS)
                nodes.forEach { node ->
                    Tasks.await(
                        Wearable.getMessageClient(this@MainActivity)
                            .sendMessage(node.id, SETTINGS_REQUEST_PATH, ByteArray(0)),
                        10,
                        TimeUnit.SECONDS,
                    )
                }
            } catch (_: Exception) {
            }
        }
    }

    private fun strings(): WearStrings = wearStrings(preferredLanguage)

    private fun localizeError(errorCode: String, fallback: String?): String = when (errorCode) {
        "missing_access_token" -> strings().text(WatchStringKey.MISSING_ACCESS_TOKEN)
        "report_cooldown" -> strings().text(WatchStringKey.REPORT_COOLDOWN)
        "restricted_account" -> strings().text(WatchStringKey.RESTRICTED_ACCOUNT)
        else -> fallback ?: strings().text(WatchStringKey.QUICK_REPORT_FAILED)
    }

    @SuppressLint("MissingPermission")
    private suspend fun getCurrentLocation() =
        Tasks.await(LocationServices.getFusedLocationProviderClient(this).lastLocation, 10, TimeUnit.SECONDS)
}

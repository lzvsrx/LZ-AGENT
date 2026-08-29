package dev.lzagent.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.unit.dp
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { LzAgentScreen(::sendMessage) }
    }

    private fun sendMessage(message: String, privateMode: Boolean, completed: (Result<String>) -> Unit) {
        Executors.newSingleThreadExecutor().execute {
            val result = runCatching {
                val connection = URL("${BuildConfig.AGENT_URL}/api/v1/chat").openConnection() as HttpURLConnection
                try {
                    connection.requestMethod = "POST"
                    connection.connectTimeout = 3_000
                    connection.readTimeout = 30_000
                    connection.doOutput = true
                    connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    val body = chatPayload(ChatCommand(message, privateMode))
                    connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                    if (connection.responseCode !in 200..299) error("HTTP ${connection.responseCode}")
                    JSONObject(connection.inputStream.bufferedReader().use { it.readText() }).getString("text")
                } finally {
                    connection.disconnect()
                }
            }
            runOnUiThread { completed(result) }
        }
    }
}

@androidx.compose.runtime.Composable
private fun LzAgentScreen(send: (String, Boolean, (Result<String>) -> Unit) -> Unit) {
    var message by remember { mutableStateOf("") }
    var privateMode by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var response by remember { mutableStateOf("Pronto para ajudar.") }

    MaterialTheme(colorScheme = darkColorScheme(primary = androidx.compose.ui.graphics.Color(0xFF00CBEF))) {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier.padding(24.dp).verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text("LZ Agent", style = MaterialTheme.typography.headlineLarge, modifier = Modifier.semantics { heading() })
                Text("Agente pessoal local, acessível e auditável")
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Modo privado")
                    Switch(checked = privateMode, onCheckedChange = { privateMode = it })
                }
                OutlinedTextField(
                    value = message,
                    onValueChange = { message = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("O que você precisa?") },
                    enabled = !busy,
                    minLines = 3,
                )
                Button(
                    enabled = !busy,
                    onClick = {
                        val trimmed = message.trim()
                        val error = validatePrompt(trimmed)
                        if (error != null) {
                            response = error
                        } else {
                            busy = true
                            response = "Processando…"
                            send(trimmed, privateMode) { result ->
                                busy = false
                                response = result.getOrElse {
                                    "Núcleo local indisponível. Inicie o servidor e execute a tarefa adb reverse."
                                }
                            }
                        }
                    },
                ) { Text(if (busy) "Aguarde" else "Enviar") }
                Text(response, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
            }
        }
    }
}

internal fun validatePrompt(message: String): String? =
    if (message.isBlank()) "Digite uma solicitação antes de enviar." else null

internal data class ChatCommand(val message: String, val privateMode: Boolean)

internal fun chatPayload(command: ChatCommand): String =
    JSONObject().put("message", command.message).put("private", command.privateMode).toString()

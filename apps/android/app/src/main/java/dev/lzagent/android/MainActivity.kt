package dev.lzagent.android

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    private var accessToken: String? = null
    private var pendingVoiceResult: ((Result<String>) -> Unit)? = null
    private var speechRecognizer: SpeechRecognizer? = null
    private val microphonePermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) beginRecognition()
            else finishVoice(Result.failure(IllegalStateException("Permissão de microfone negada.")))
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { LzAgentScreen(::login, ::sendMessage, ::startVoiceInput) }
    }

    override fun onDestroy() {
        speechRecognizer?.destroy()
        speechRecognizer = null
        super.onDestroy()
    }

    private fun startVoiceInput(completed: (Result<String>) -> Unit) {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            completed(Result.failure(IllegalStateException("Reconhecimento de fala indisponível.")))
            return
        }
        pendingVoiceResult = completed
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        ) {
            beginRecognition()
        } else {
            microphonePermission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun beginRecognition() {
        speechRecognizer?.destroy()
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).also { recognizer ->
            recognizer.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) = Unit
                override fun onBeginningOfSpeech() = Unit
                override fun onRmsChanged(rmsdB: Float) = Unit
                override fun onBufferReceived(buffer: ByteArray?) = Unit
                override fun onEndOfSpeech() = Unit
                override fun onPartialResults(partialResults: Bundle?) = Unit
                override fun onEvent(eventType: Int, params: Bundle?) = Unit
                override fun onError(error: Int) = finishVoice(
                    Result.failure(IllegalStateException(speechErrorMessage(error))),
                )

                override fun onResults(results: Bundle?) {
                    val text = results
                        ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        ?.firstOrNull()
                        ?.trim()
                    if (text.isNullOrEmpty()) {
                        finishVoice(Result.failure(IllegalStateException("Nenhuma fala reconhecida.")))
                    } else {
                        finishVoice(Result.success(text))
                    }
                }
            })
            recognizer.startListening(Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toLanguageTag())
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            })
        }
    }

    private fun finishVoice(result: Result<String>) {
        pendingVoiceResult?.invoke(result)
        pendingVoiceResult = null
        speechRecognizer?.destroy()
        speechRecognizer = null
    }

    private fun login(username: String, password: String, completed: (Result<Unit>) -> Unit) {
        Executors.newSingleThreadExecutor().execute {
            val result = runCatching {
                val connection = URL("${BuildConfig.AGENT_URL}/api/v1/auth/login").openConnection() as HttpURLConnection
                try {
                    connection.requestMethod = "POST"
                    connection.connectTimeout = 3_000
                    connection.readTimeout = 15_000
                    connection.doOutput = true
                    connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    val body = JSONObject().put("username", username).put("password", password).toString()
                    connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                    if (connection.responseCode !in 200..299) error("HTTP ${connection.responseCode}")
                    accessToken = JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
                        .getString("access_token")
                } finally {
                    connection.disconnect()
                }
            }
            runOnUiThread { completed(result) }
        }
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
                    accessToken?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
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
private fun LzAgentScreen(
    authenticate: (String, String, (Result<Unit>) -> Unit) -> Unit,
    send: (String, Boolean, (Result<String>) -> Unit) -> Unit,
    listen: ((Result<String>) -> Unit) -> Unit,
) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
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
                OutlinedTextField(
                    value = username,
                    onValueChange = { username = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Usuário") },
                    singleLine = true,
                    enabled = !busy,
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Senha") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    enabled = !busy,
                )
                Button(
                    enabled = !busy && username.isNotBlank() && password.isNotEmpty(),
                    onClick = {
                        busy = true
                        response = "Autenticando…"
                        authenticate(username.trim(), password) { result ->
                            busy = false
                            result.onSuccess {
                                password = ""
                                response = "Login concluído para esta sessão do aplicativo."
                            }.onFailure {
                                response = "Não foi possível entrar. Verifique usuário, senha e núcleo local."
                            }
                        }
                    },
                ) { Text("Entrar") }
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
                        response = "Ouvindo…"
                        listen { result ->
                            result.onSuccess {
                                message = it
                                response = "Fala convertida em texto. Revise antes de enviar."
                            }.onFailure {
                                response = it.message ?: "Não foi possível reconhecer a fala."
                            }
                        }
                    },
                ) { Text("Usar microfone") }
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

internal fun speechErrorMessage(error: Int): String = when (error) {
    SpeechRecognizer.ERROR_AUDIO -> "Falha ao capturar o áudio."
    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Permissão de microfone insuficiente."
    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
        "O serviço de fala precisa de rede ou não respondeu."
    SpeechRecognizer.ERROR_NO_MATCH -> "Não foi possível compreender a fala."
    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "O reconhecedor de fala está ocupado."
    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Nenhuma fala foi detectada."
    else -> "O reconhecimento de fala falhou (código $error)."
}

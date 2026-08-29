package dev.lzagent.android

import android.speech.SpeechRecognizer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MainActivityTest {
    @Test
    fun emptyPromptIsRejected() {
        assertEquals("Digite uma solicitação antes de enviar.", validatePrompt("   "))
        assertNull(validatePrompt("Olá"))
    }

    @Test
    fun commandPreservesMessageAndPrivateMode() {
        val command = ChatCommand("Olá, mundo", true)
        assertEquals("Olá, mundo", command.message)
        assertEquals(true, command.privateMode)
    }

    @Test
    fun speechErrorsHaveAccessibleMessages() {
        assertEquals("Nenhuma fala foi detectada.", speechErrorMessage(SpeechRecognizer.ERROR_SPEECH_TIMEOUT))
        assertEquals("Permissão de microfone insuficiente.", speechErrorMessage(SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS))
    }
}

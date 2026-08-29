package dev.lzagent.android

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
}

# Matriz de suporte por capacidade

Atualizada em 29/08/2026. Marca/modelo não é garantia: o agente detecta capacidades e mantém fallback
textual. `Compila` não significa que todos os aparelhos daquela família foram validados.

| Plataforma | Forma de acesso | Arquitetura | Estado verificável |
|---|---|---|---|
| Windows 11 | WinUI 3 + web/PWA | x64 validado; ARM64 planejado | build CI; dispositivo/microfone no núcleo |
| Android 8+ | Compose + web/PWA | arm64 e emulador x86_64 | APK, lint, testes e fala opt-in compilados |
| Linux moderno | Flutter + web/PWA | x86_64 validado; aarch64 planejado | análise/testes/build CI |
| ChromeOS | web/PWA; APK quando compatível | depende do aparelho | implementação disponível; teste físico pendente |
| macOS | web/PWA | Apple Silicon/x64 | implementação web disponível; testes nativos pendentes |
| iPhone/iPad | web/PWA | Apple Silicon | implementação web disponível; testes Safari pendentes |
| HarmonyOS e derivados | web responsiva quando compatível | depende do aparelho | não validado; cliente nativo inexistente |
| TVs, relógios, carros e IoT | web apenas quando adequada | variável | não suportado até existir UX e teste específicos |

## Critérios para declarar suporte

1. instalação, abertura e atualização testadas em aparelho real;
2. teclado/toque, leitor de tela, escala de fonte, RTL e redução de movimento;
3. rede, modo offline, suspensão, bateria e permissões;
4. microfone/STT/TTS por locale com fallback textual;
5. autenticação, armazenamento seguro, exclusão e logs;
6. desempenho Lite/Standard/Pro;
7. política da loja, assinatura, privacidade e requisitos legais do território.

A PWA guarda somente o shell estático. APIs, conversas e respostas privadas nunca entram no cache do
service worker. O núcleo local ainda precisa estar acessível para chat, memória e ferramentas.

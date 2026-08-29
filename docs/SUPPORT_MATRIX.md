# Matriz de suporte inicial

| Plataforma | Arquiteturas prioritárias | Estado 0.1.0 |
|---|---|---|
| Windows 11 | x64; ARM64 planejado | API/UI local em validação |
| Linux moderno | x86_64; aarch64 planejado | API/UI local em validação; Flatpak planejado |
| Android | arm64-v8a; emulador x86_64 | cliente Compose planejado |

Perfis: Lite usa CPU e fallback local/nuvem; Standard habilita recursos equilibrados; Pro pode usar
GPU/NPU e modelos maiores. A presença de aceleração nunca elimina o fallback.


# Auditoria de implementação do Documento Mestre 2026

Atualizado em 30/08/2026. Esta matriz compara o PDF canônico com código, testes e artefatos reais.
`Parcial` não significa suporte de produção e `planejado` não deve aparecer como funcional em releases.

| Requisito do documento | Estado | Evidência atual | Próximo critério de conclusão |
|---|---|---|---|
| Núcleo separado das interfaces | Parcial funcional | FastAPI, serviços, políticas e clientes HTTP separados | autenticação IPC e execução de tarefas longa |
| Windows WinUI 3 | Parcial funcional | build x64, login e chat autenticado acessível | notificações, deep links, tray, ARM64 e MSIX assinado |
| Android Compose | Parcial funcional | build CLI/VS Code, login, chat, fala opt-in, lint e APK | UI adaptativa, instrumentação TalkBack/Switch Access e assinatura |
| Linux Flutter | Parcial funcional | login/chat, análise/widget tests, tar.gz e manifesto/build Flatpak 25.08 na CI | Portals nativos e matriz real Wayland/X11/distribuições |
| Action Ledger | Parcial funcional | chat, documentos, memória e sugestões auditados | duração, erros, aprovação e modelo em toda ferramenta |
| Memória por projeto | Parcial funcional | projetos/lições editáveis, busca por texto/escopo, retenção do ledger, expurgo confirmado, sugestões, exportação, exclusão, backup e restauração SQLite verificados | fontes/artefatos editáveis, criptografia por plataforma e retenção por projeto/sessão |
| Suggestion Engine | Parcial funcional | sugestão com justificativa/origem e decisão do usuário | geração contextual, ranking e explicação entre projetos |
| Checkpoint/diff/rollback | Parcial funcional | checkpoint captura commit, arquivos e diff Git limitado; restauração cria backup de segurança | aplicação/reversão de patch com confirmação e testes pós-mudança |
| IA própria do agente | Núcleo nativo inicial | `native-core-v1` local, auditável e sem Ollama/provedor externo | corpus licenciado, treinamento, pesos próprios, avaliações e assinatura |
| Paridade de capacidades de IA | Matriz definida | roadmap separa conversa, código, pesquisa, multimodal, ferramentas e avaliações | implementar e aprovar cada gate sem copiar tecnologia proprietária |
| Pesquisa na internet | Parcial funcional | busca consentida, leitura limitada, auditoria e bloqueio de rede privada | múltiplas fontes, citações no chat, cache/robots e defesa contra prompt injection |
| Texto e idiomas globais | Infraestrutura parcial | BCP 47, fallback, RTL, `pt-BR` e `en` | catálogos revisados por falantes e testes de layout/formato |
| STT/TTS | Detecção parcial | registro impede anunciar voz não verificada | engines locais/sistema, consentimento cloud e testes por locale |
| Imagens/documentos | Parcial funcional | metadados de imagem/PDF/texto sem retenção | OCR, descrição semântica autorizada e câmera |
| Plugins | Parcial seguro/fail-closed | SHA-256, grants, aprovação, JSON limitado, timeout, Bubblewrap sem rede no Linux e bloqueio sem sandbox | helper LPAC/AppContainer assinado no Windows, cancelamento cooperativo e assinatura de terceiros |
| Perfis Lite/Standard/Pro | Detecção parcial | diagnóstico básico de hardware | roteamento de capacidades e testes em hardware-alvo |
| Acessibilidade combinável | Parcial | semântica/foco/teclado/live regions iniciais | auditorias manuais e automáticas por plataforma e perfis persistentes |
| Avatar 2D/3D | Parcial funcional | `.blend` mestre, três GLBs, 32 ossos, 13 clips, preview e API de estados | integrar renderer nos clientes, revisar deformações/gestos e otimizar em aparelhos reais |
| Segurança e privacidade | Parcial | políticas, modo privado, exclusão, docs e segredos ignorados | cofre do SO, sandbox, threat tests, assinatura e SBOM |
| Cadastro e login | Parcial funcional | conta local, Argon2id, rotas protegidas e login nos três clientes nativos | recuperação, persistência no cofre do SO e testes de dispositivo |
| Dispositivo e sistema | Parcial funcional | tipo, SO/versão, arquitetura, CPU e nome opt-in | registro consentido entre dispositivos e matriz por hardware |
| Microfone e fala | Parcial funcional | entradas no núcleo, ditado web e reconhecimento Android opt-in com fallback | STT local consistente em Windows/Linux e testes multilíngues |
| Sincronização PostgreSQL | Planejado | contrato e política desativada | protocolo E2EE/autenticado, conflitos e consentimento |
| Instaladores e atualização | Planejado | workflows e builds de desenvolvimento | MSIX/APK/Flatpak assinados, atualização, rollback e teste limpo |
| Releases GitHub | Parcial funcional | CI e pré-releases com Windows/Android/Linux/Python/fontes, SHA-256 e SBOM Python CycloneDX | assinatura com identidade protegida, SBOMs nativos e promoção estável |
| Conformidade mundial | Processo parcial | matriz inicial Brasil/SP, UE, Reino Unido e EUA | revisão jurídica por país/estado/setor antes de declarar suporte |
| Série de vídeos | Planejado | estrutura descrita no PDF | roteiros, gravação, legendas e release reproduzível por episódio |
| Unity/Unreal/Godot por código | Política definida | fontes/configurações versionadas e builds headless/CLI obrigatórios | runners isolados e projetos reais testados em CI por motor |

## Ordem de implementação recomendada

1. Completar governança de memória: fontes/artefatos, criptografia por plataforma e retenção por projeto/sessão.
2. Implementar e auditar helper LPAC/AppContainer assinado antes de executar plugins no Windows.
3. Implementar um provedor real e um local atrás do mesmo contrato, com consentimento e métricas.
4. Fechar acessibilidade e empacotamento de um fluxo principal em Windows, Android e Linux.
5. Adicionar STT/TTS e visão por capacidade verificada, sempre com fallback textual.
6. Somente então ampliar automação, sincronização, avatar 3D e catálogo de profissões.

## Linguagens e tecnologias: lacunas para uma versão estável

O Documento Mestre afirma que “usar todas as linguagens” não é uma meta. A versão 1.0 deve usar cada
linguagem somente onde ela reduz risco ou fornece integração nativa. O repositório já contém Python
(núcleo/API), C#/XAML (Windows), Kotlin/Compose (Android), Dart/Flutter/C++ do runner (Linux),
TypeScript/JavaScript/HTML/CSS (web), SQL (persistência), PowerShell e YAML (automação/release), além
de Python/Blender e glTF para o avatar.

| Tecnologia citada no documento | Situação real | Decisão para 1.0 |
|---|---|---|
| Rust | não implementado | não é bloqueador; adotar somente após benchmark e revisão de segurança demonstrarem necessidade em sandbox, multimídia ou inferência |
| C++ próprio | apenas código gerado/runner Flutter | não adicionar por paridade nominal; manter isolado às integrações nativas que realmente exigirem ABI C/C++ |
| PostgreSQL | contrato planejado; sem implementação operacional | não bloquear a edição local 1.0; necessário apenas antes de anunciar sincronização multi-dispositivo |
| STT/TTS nativo multiplataforma | parcial | bloqueia anunciar voz completa; implementar adaptadores por sistema, consentimento, fallback textual e testes por locale |
| Criptografia/cofre por sistema | parcial | bloqueia versão estável: Windows Credential Locker/DPAPI, Android Keystore e Secret Service/libsecret no Linux |
| Instaladores e atualização assinados | parcial | bloqueia versão estável: MSIX/APK/Flatpak assinados, atualização, rollback e instalação limpa testada |
| SBOM nativo e proveniência | parcial | bloqueia promoção estável: SBOM de Python, .NET, Android e Flutter, checksums e artefatos vinculados ao commit/tag |

### Gates obrigatórios de promoção

- **Beta:** fluxo login → conversa → aprovação → auditoria passa em Windows, Android e Linux; testes de acessibilidade e dispositivos reais documentados; nenhuma vulnerabilidade crítica/alta aberta.
- **Release candidate:** instaladores assinados e atualizáveis, migração/rollback testados, recuperação de conta e segredos no cofre do sistema, matriz de privacidade e licenças aprovada.
- **1.0 estável:** todos os gates anteriores repetíveis em CI, teste de instalação limpa e atualização da versão anterior, suporte e política de vulnerabilidades operacionais, revisão jurídica dos mercados efetivamente anunciados.

Adicionar Rust, Swift, mais C++ ou qualquer outra linguagem sem um requisito testável aumenta a
superfície de ataque e manutenção e não aproxima o produto da versão final.

## Regras de honestidade de release

- Nenhuma plataforma é “suportada” só porque compilou.
- Nenhum idioma é “completo” sem revisão humana e testes de texto e voz.
- Nenhuma jurisdição é “100% conforme” sem revisão jurídica aplicável ao produto e ao setor.
- Nenhuma ferramenta pode executar apenas porque seu plugin foi instalado.
- Todo item pendente nesta matriz continua sendo requisito, não promessa já entregue.

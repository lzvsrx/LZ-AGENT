# Auditoria de implementação do Documento Mestre 2026

Atualizado em 30/08/2026. Esta matriz compara o PDF canônico com código, testes e artefatos reais.
`Parcial` não significa suporte de produção e `planejado` não deve aparecer como funcional em releases.

| Requisito do documento | Estado | Evidência atual | Próximo critério de conclusão |
|---|---|---|---|
| Núcleo separado das interfaces | Parcial funcional | FastAPI, serviços, políticas e clientes HTTP separados | autenticação IPC e execução de tarefas longa |
| Windows WinUI 3 | Parcial funcional | build x64, login e chat autenticado acessível | notificações, deep links, tray, ARM64 e MSIX assinado |
| Android Compose | Parcial funcional | build CLI/VS Code, login, chat, fala opt-in, lint e APK | UI adaptativa, instrumentação TalkBack/Switch Access e assinatura |
| Linux Flutter | Parcial funcional | login/chat, análise e testes de widget; build Linux na CI | Portals, Flatpak e matriz Wayland/X11 |
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
| Plugins | Parcial funcional | esquema, quatro plugins executáveis, grants, aprovação, JSON limitado, subprocesso, timeout e auditoria | sandbox forte AppContainer/seccomp/Flatpak, cancelamento cooperativo e assinatura de terceiros |
| Perfis Lite/Standard/Pro | Detecção parcial | diagnóstico básico de hardware | roteamento de capacidades e testes em hardware-alvo |
| Acessibilidade combinável | Parcial | semântica/foco/teclado/live regions iniciais | auditorias manuais e automáticas por plataforma e perfis persistentes |
| Avatar 2D/3D | Parcial funcional | `.blend` mestre, três GLBs, 32 ossos, 13 clips, preview e API de estados | integrar renderer nos clientes, revisar deformações/gestos e otimizar em aparelhos reais |
| Segurança e privacidade | Parcial | políticas, modo privado, exclusão, docs e segredos ignorados | cofre do SO, sandbox, threat tests, assinatura e SBOM |
| Cadastro e login | Parcial funcional | conta local, Argon2id, rotas protegidas e login nos três clientes nativos | recuperação, persistência no cofre do SO e testes de dispositivo |
| Dispositivo e sistema | Parcial funcional | tipo, SO/versão, arquitetura, CPU e nome opt-in | registro consentido entre dispositivos e matriz por hardware |
| Microfone e fala | Parcial funcional | entradas no núcleo, ditado web e reconhecimento Android opt-in com fallback | STT local consistente em Windows/Linux e testes multilíngues |
| Sincronização PostgreSQL | Planejado | contrato e política desativada | protocolo E2EE/autenticado, conflitos e consentimento |
| Instaladores e atualização | Planejado | workflows e builds de desenvolvimento | MSIX/APK/Flatpak assinados, atualização, rollback e teste limpo |
| Releases GitHub | Parcial funcional | repositório, CI e pré-releases com Windows/Android/Linux/Python/fontes | assinatura, SBOM, checksums destacados e promoção estável |
| Conformidade mundial | Processo parcial | matriz inicial Brasil/SP, UE, Reino Unido e EUA | revisão jurídica por país/estado/setor antes de declarar suporte |
| Série de vídeos | Planejado | estrutura descrita no PDF | roteiros, gravação, legendas e release reproduzível por episódio |
| Unity/Unreal/Godot por código | Política definida | fontes/configurações versionadas e builds headless/CLI obrigatórios | runners isolados e projetos reais testados em CI por motor |

## Ordem de implementação recomendada

1. Completar governança de memória: fontes/artefatos, criptografia por plataforma e retenção por projeto/sessão.
2. Endurecer o runner de plugins com sandbox nativa por SO antes de aceitar terceiros.
3. Implementar um provedor real e um local atrás do mesmo contrato, com consentimento e métricas.
4. Fechar acessibilidade e empacotamento de um fluxo principal em Windows, Android e Linux.
5. Adicionar STT/TTS e visão por capacidade verificada, sempre com fallback textual.
6. Somente então ampliar automação, sincronização, avatar 3D e catálogo de profissões.

## Regras de honestidade de release

- Nenhuma plataforma é “suportada” só porque compilou.
- Nenhum idioma é “completo” sem revisão humana e testes de texto e voz.
- Nenhuma jurisdição é “100% conforme” sem revisão jurídica aplicável ao produto e ao setor.
- Nenhuma ferramenta pode executar apenas porque seu plugin foi instalado.
- Todo item pendente nesta matriz continua sendo requisito, não promessa já entregue.

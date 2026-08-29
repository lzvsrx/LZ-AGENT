# LZ Agent

**Seu agente pessoal inteligente — multimodal, acessível, extensível e orientado a tarefas.**

O LZ Agent é uma plataforma de assistência pessoal para Windows, Android e Linux. O projeto não
pretende ser apenas uma tela de chat: seu núcleo separa conversa, planejamento, políticas,
ferramentas, memória, aprendizado controlado, provedores de IA e interfaces de plataforma. Essa
separação permite substituir modelos e clientes sem perder contratos, histórico autorizado ou
controle do usuário.

Este monorepo implementa o [Documento Mestre Completo 2026](docs/specification/LZ_AGENT_DOCUMENTO_MESTRE_COMPLETO_2026.pdf).
O documento é uma especificação de produto; o código e os testes versionados são a fonte de verdade
da implementação. Conceitos históricos que contrariem a especificação atual, como dependência de
Docker, permanecem apenas no arquivo visual e não fazem parte da arquitetura.

> [!IMPORTANT]
> O projeto está em desenvolvimento alfa. O núcleo local, a interface web e o cliente Windows já
> possuem partes executáveis e testadas; Android e Linux possuem clientes iniciais, enquanto voz completa, visão semântica, sincronização,
> avatar 3D e instaladores finais ainda não devem ser anunciados como suporte de produção.

## Por que o projeto existe

Assistentes pessoais normalmente concentram dados, automação e decisões em uma caixa-preta. O LZ
Agent adota o caminho oposto:

- registra o que o agente **faz**, sem coletar indiscriminadamente tudo que a pessoa vê ou fala;
- exige consentimento para ações destrutivas, publicação, dados sensíveis e serviços externos;
- mantém memória por projeto pesquisável, exportável e apagável;
- transforma correções em lições explícitas com evidência e confiança, sem retreinar silenciosamente
  um modelo-base;
- usa provedores intercambiáveis e fallback local, evitando dependência arquitetural de uma empresa;
- considera acessibilidade, privacidade e redução de movimento como requisitos de engenharia;
- detecta capacidades do hardware e degrada de Lite/Standard/Pro sem quebrar a função essencial.

## Estado verificável

| Área | Estado atual | Evidência |
|---|---|---|
| Núcleo Python/FastAPI | funcional em modo local | API, testes e health check |
| SQLite e migrações | funcional | schemas `0001`/`0002`, foreign keys e WAL |
| Action Ledger | funcional | chat, memória e documentos geram ações auditáveis |
| Memória de projetos | funcional inicial | criar, listar, exportar e apagar com confirmação |
| Aprendizado controlado | funcional inicial | lições com problema, solução, evidência e confiança |
| Políticas de segurança | funcional inicial | risco sensível sempre exige aprovação explícita |
| Plugins | descoberta/validação funcional | quatro manifestos validados; execução isolada continua em construção |
| Idiomas | infraestrutura funcional | BCP 47, variantes regionais, fallback e RTL; `pt-BR`/`en` iniciais |
| STT/TTS | registro de capacidades funcional | voz não verificada nunca é anunciada ou escolhida |
| Documentos/visão | inspeção local funcional | PNG/JPEG/WebP/GIF, texto e PDF sem retenção por padrão |
| Interface web | funcional | responsiva, teclado, foco, live region, contraste e movimento reduzido |
| Windows WinUI 3 | compila e acessa a API | build x64 com 0 erros/avisos |
| Android Compose | cliente inicial funcional | build nativo por CLI/VS Code, testes e lint; Android Studio não é necessário |
| Linux/Flutter/Flatpak | cliente Flutter funcional inicial | análise e testes de widgets passam; pacote Flatpak pendente |
| Avatar 2D/3D | marca 2D inicial | SVG/PNG/ICO canônicos; GLB, rig, LOD e animações pendentes |
| Releases | automação preparada | CI e workflow de tag; publicação depende de autenticação GitHub |

O número de testes e o suporte declarado mudam com o desenvolvimento. Execute os comandos abaixo em
vez de confiar em um número escrito no README.

## Stack fixada

O baseline completo fica em [`versions/technology-baseline.json`](versions/technology-baseline.json).
As versões centrais verificadas em 29/08/2026 incluem:

- Python 3.14.7 e FastAPI 0.141.1;
- .NET SDK 10.0.400, C# 14, Windows App SDK 2.4.0 e Windows SDK 10.0.28000.2705;
- JDK 17, Kotlin 2.4.10, Android Gradle Plugin 9.3.2 e Gradle 9.5.0;
- Flutter 3.47.0 e Dart 3.13.0 para o cliente Linux;
- Rust 1.98.0 para componentes críticos quando houver justificativa de desempenho;
- SQLite 3.53.4 local e PostgreSQL 18.6 opcional para sincronização futura;
- Blender 5.2.1 LTS e FFmpeg 9.0.1 para 3D e mídia.

Versão “mais recente” não entra automaticamente. Dependabot pode propor atualizações, mas a promoção
exige notas oficiais, compatibilidade, migração, testes, acessibilidade, desempenho e rollback. Isso
evita que uma atualização aparentemente simples quebre clientes ou dados persistentes.

## Executar o núcleo local

Requer Python 3.14.7 e Git. No PowerShell, a partir da raiz do repositório:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m lz_agent.main
```

Abra:

- interface: <http://127.0.0.1:8765>;
- documentação OpenAPI: <http://127.0.0.1:8765/docs>;
- saúde: <http://127.0.0.1:8765/api/v1/system/health>;
- capacidades instaladas: <http://127.0.0.1:8765/api/v1/system/capabilities>.

Sem chave externa, o agente permanece utilizável no fallback local determinístico. Ele registra a
solicitação e informa com clareza que um modelo de IA não foi acionado; nunca simula uma execução que
não aconteceu.

## Cliente Windows

O projeto [`apps/windows/LzAgent.Windows.csproj`](apps/windows/LzAgent.Windows.csproj) usa WinUI 3 e
Windows App SDK 2.4.0. Inicie primeiro o núcleo Python e então compile:

```powershell
& 'C:\Program Files\dotnet\dotnet.exe' build apps/windows/LzAgent.Windows.csproj -c Debug -p:Platform=x64
& 'C:\Program Files\dotnet\dotnet.exe' run --project apps/windows/LzAgent.Windows.csproj -p:Platform=x64
```

O cliente oferece navegação para Home, Tarefas, Ferramentas, Memória, Acessibilidade, Dispositivos e
Desenvolvedor, modo privado e anúncio de estados para tecnologias assistivas. Áreas ainda não
implementadas não fingem funcionalidade: mostram o contrato ao qual serão conectadas.

## Cliente Android no VS Code

O projeto [`apps/android`](apps/android) usa Kotlin, Jetpack Compose, AGP 9.3.2 e Gradle Wrapper. Ele
é compilado integralmente por linha de comando; **Android Studio não é necessário**. No terminal do
VS Code:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-android.ps1
cd apps\android
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug
adb reverse tcp:8765 tcp:8765
.\gradlew.bat installDebug
```

As mesmas operações estão em `Terminal > Run Task`: preparar SDK, verificar, listar dispositivos,
encaminhar a API local e instalar o APK. O `adb reverse` liga o aplicativo no aparelho ao núcleo em
`127.0.0.1:8765` no computador. Consulte
[`docs/development/android-vscode.md`](docs/development/android-vscode.md).

## Cliente Linux

O cliente em [`apps/linux`](apps/linux) usa Flutter/Dart e compartilha o contrato HTTP do núcleo.
No Windows é possível analisar e testar os widgets; o binário Linux e o Flatpak são produzidos em
um runner Linux:

```powershell
cd apps\linux
..\..\.toolchains\flutter\bin\flutter.bat analyze
..\..\.toolchains\flutter\bin\flutter.bat test
```

## Idiomas, texto e áudio

O programa usa códigos BCP 47 e preserva região/script — por exemplo `pt-BR`, `pt-PT`, `es-MX`,
`zh-Hans-CN` e `zh-Hant-TW`. O fallback é `idioma-região → idioma → inglês`, sempre detectável. A
direção RTL é determinada por idioma/script e o usuário pode substituir a detecção automática.

A meta é aceitar todos os locales válidos e expandir STT/TTS para todas as línguas tecnicamente
disponíveis, mas nenhuma língua entra como “verificada” sem revisão por falante nativo e testes de
texto, plural, formatos, layout, acessibilidade, transcrição e voz. Quando não existe voz adequada, o
fallback correto é texto — nunca uma voz de outro idioma escolhida silenciosamente.

Veja [`docs/INTERNATIONALIZATION.md`](docs/INTERNATIONALIZATION.md).

## Memória, privacidade e aprendizado

SQLite é o backend local padrão. O schema armazena ações, projetos, decisões, lições, sugestões,
artefatos, preferências, fontes, checkpoints e versões técnicas. Conteúdo de sessão privada não é
persistido. A inspeção de documentos calcula metadados/hash e processa o arquivo em memória sem
retê-lo por padrão.

Fluxo de mudança relevante:

```text
analisar → checkpoint → política/aprovação → alterar → diff → testar → registrar → manter ou rollback
```

Segredos ficam fora do repositório. Copie `.env.example` para `.env` somente quando habilitar um
provedor externo; `.env`, bancos, backups, caches, certificados e ambientes virtuais são ignorados.

## Plugins

Cada plugin possui ID, versão, descrição, comandos, permissões e entrypoint. O registro rejeita
manifestos incompletos, IDs inválidos e permissões/comandos duplicados. Instalação não concede
permissão nem execução. Os pacotes iniciais são Produtividade, Desenvolvedor, Mídia e Blender.

O próximo nível inclui grants persistentes, sandbox, entrada/saída validada, timeout, cancelamento e
registro de toda execução no Action Ledger.

## Testes e diagnóstico

```powershell
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m pytest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verify-stack.ps1 -Strict
& 'C:\Program Files\dotnet\dotnet.exe' build apps/windows/LzAgent.Windows.csproj -c Debug -p:Platform=x64
```

Para auditar dependências NuGet:

```powershell
dotnet list apps/windows/LzAgent.Windows.csproj package --vulnerable --include-transitive
dotnet list apps/windows/LzAgent.Windows.csproj package --outdated
```

Os assets Windows são derivados deterministicamente do SVG oficial:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\generate-brand-assets.ps1
```

## Estrutura do monorepo

```text
apps/                 clientes web, Windows, Android e Linux
assets/               marca, avatar e arquivo conceitual histórico
config/               configuração canônica sem segredos
core/agent/            orquestração, API, memória, políticas e provedores
data/migrations/       migrações SQLite versionadas
docs/                  arquitetura, acessibilidade, segurança, jurídico e releases
plugins/               capacidades isoladas por manifesto/permissão
scripts/               diagnóstico, geração de assets, build e empacotamento
shared/localization/   catálogos e política global de idiomas
shared/schemas/        contratos JSON entre clientes e núcleo
tests/                 testes automatizados
versions/              baseline técnico reproduzível
```

## Acessibilidade

A referência é WCAG 2.2 AA, complementada por Narrator/WinUI, TalkBack/Compose e tecnologias Linux.
Tudo que depende de mouse/toque deve ter alternativa por teclado, voz ou ação acessível quando
aplicável. Estado importante nunca depende apenas de cor, som, gesto ou animação. Interfaces devem
respeitar escala de texto, alto contraste e redução de movimento.

Consulte [`docs/ACCESSIBILITY.md`](docs/ACCESSIBILITY.md).

## Segurança e conformidade

O modelo de segurança usa privilégio mínimo, allowlist, confirmação para ações sensíveis, logs
compreensíveis e retenção configurável. A matriz jurídica cobre a base de engenharia para Brasil/São
Paulo, UE/EEE, Reino Unido, EUA e gates de lançamento para outros territórios. Ela não substitui
parecer jurídico local: país e setor só podem ser marcados como suportados após revisão aplicável.

- [`SECURITY.md`](SECURITY.md): reporte privado de vulnerabilidades;
- [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md): controles técnicos;
- [`docs/LEGAL_COMPLIANCE.md`](docs/LEGAL_COMPLIANCE.md): matriz jurídica e fontes oficiais;
- [`docs/SUPPORT_MATRIX.md`](docs/SUPPORT_MATRIX.md): plataformas e arquiteturas validadas.

## CI, versionamento e releases

Commits passam por lint, testes Python e build Windows. Tags `v*` acionam geração de wheel, source
archive e artefatos de plataforma que estiverem realmente validados. Binários nativos não entram na
release só porque compilam: assinatura, instalação limpa, acessibilidade, matriz de dispositivos,
licenças, vulnerabilidades e rollback também são gates.

Veja [`docs/RELEASE_PROCESS.md`](docs/RELEASE_PROCESS.md) e [`CHANGELOG.md`](CHANGELOG.md).

## Contribuição

Abra uma issue com critérios de aceitação, faça uma alteração pequena, revise o diff e execute os
testes proporcionais ao risco. Dependências novas precisam de finalidade, licença, fonte oficial e
plano de remoção/rollback. Consulte [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licença e assets

A licença de distribuição do código ainda precisa ser formalmente confirmada pelo proprietário antes
da primeira release pública estável. As duas imagens do anexo do Documento Mestre são preservadas em
`assets/concept-history` como referência histórica; sua presença não concede automaticamente direitos
de reutilização fora do projeto. Proveniência e licença do avatar 3D, áudio e datasets serão gates de
release.

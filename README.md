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

O acompanhamento requisito por requisito fica em
[`docs/SPEC_IMPLEMENTATION_STATUS.md`](docs/SPEC_IMPLEMENTATION_STATUS.md); a matriz separa o que
funciona, o que é parcial e o que ainda está planejado.

A comparação testável de conversa, código, pesquisa, voz, visão, memória, ferramentas e outras
capacidades de IA fica em [`docs/AI_CAPABILITY_ROADMAP.md`](docs/AI_CAPABILITY_ROADMAP.md).
Autoria, dependências e assets são separados em
[`docs/ORIGINALITY_AND_PROVENANCE.md`](docs/ORIGINALITY_AND_PROVENANCE.md) e no manifesto
`versions/component-provenance.json`.

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
| Memória de projetos | funcional inicial | criar, editar, pesquisar, reter, exportar e apagar com confirmação |
| Aprendizado controlado | funcional inicial | lições com problema, solução, evidência e confiança |
| Políticas de segurança | funcional inicial | risco sensível sempre exige aprovação explícita |
| Plugins | descoberta/validação funcional | quatro manifestos validados; execução isolada continua em construção |
| Idiomas | infraestrutura funcional | BCP 47, variantes regionais, fallback e RTL; `pt-BR`/`en` iniciais |
| STT/TTS | registro de capacidades funcional | voz não verificada nunca é anunciada ou escolhida |
| Documentos/visão | inspeção local funcional | PNG/JPEG/WebP/GIF, texto e PDF sem retenção por padrão |
| Interface web | funcional | responsiva, teclado, foco, live region, contraste e movimento reduzido |
| Web/PWA multiplataforma | funcional inicial | manifest instalável e shell offline sem cache de APIs/dados pessoais |
| Windows WinUI 3 | compila e acessa a API | build x64 com 0 erros/avisos |
| Android Compose | cliente inicial funcional | build nativo por CLI/VS Code, testes e lint; Android Studio não é necessário |
| Linux/Flutter/Flatpak | cliente e empacotamento automatizados | análise/testes, tar.gz e Flatpak validados na release; teste em distros reais pendente |
| Avatar 2D/3D | funcional inicial | `.blend`, GLB Lite/Standard/Pro, rig mecânico, 13 clips e controlador de estado |
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

O chat usa o núcleo próprio `native-core-v1`, executado dentro do LZ Agent e sem Ollama ou provedor
externo obrigatório. Esta etapa organiza, audita e encaminha tarefas; ainda não existem pesos
generativos próprios treinados, portanto o programa declara essa limitação e nunca simula uma
resposta de modelo que não aconteceu. Treinamento futuro exige corpus licenciado, avaliações e pesos
reproduzíveis e assinados.

### Preparação segura de comandos

`POST /api/v1/commands/prepare` transforma um comando em propriedades verificáveis antes da
execução: intenção, risco, permissão, capacidades, entradas ausentes, padrões seguros, necessidade de
aprovação, possibilidade de execução e fallback. O núcleo pode gerar somente padrões não sensíveis
(`locale`, modo privado, timeout limitado e auditoria). Alvos, consultas e permissões nunca são
inventados. Exclusão, internet e microfone permanecem bloqueados até consentimento explícito. Cada
preparação é registrada no Action Ledger.

## Internet e pesquisa

Pesquisa é separada da IA e não libera acesso arbitrário. `POST /api/v1/research/search` consulta uma
fonte pública somente com `approved: true`; `POST /api/v1/research/fetch` lê no máximo 1 MB de
texto/HTML/JSON, não segue redirecionamentos e bloqueia loopback, redes privadas, endereços
reservados, credenciais em URL e esquemas não HTTP(S). Toda consulta concluída entra no Action Ledger.

## Conta local e login

A API oferece cadastro, login, sessão, consulta do perfil e logout em `/api/v1/auth/*`. Senhas nunca
são armazenadas: o banco guarda somente hash Argon2id com salt aleatório. Tokens de sessão possuem
256 bits de entropia, ficam armazenados somente como SHA-256, expiram em 30 dias e podem ser
revogados. A interface web mantém o token apenas em `sessionStorage`.

Antes da primeira conta, a API permanece em modo bootstrap local. Depois dela, chat, ações, projetos,
memória, documentos, plugins, sugestões e pesquisa exigem sessão Bearer válida. Novas contas também
só podem ser criadas por uma sessão autenticada. Os clientes Windows, Android e Linux possuem
cadastro/login e enviam o token Bearer ao núcleo. A persistência desse token no cofre nativo de cada
sistema ainda é um gate antes da produção.

## Dispositivo, microfone e voz

`GET /api/v1/system/device` identifica tipo de aparelho, sistema/versão, arquitetura, processador e
CPUs lógicas. O nome do dispositivo fica oculto por padrão e o ID aleatório muda ao reiniciar o
núcleo. `GET /api/v1/audio/devices` consulta entradas PortAudio e marca o microfone padrão.

Na interface web, **Usar microfone** inicia ditado somente após ação explícita. Quando disponível, o
reconhecimento do navegador preenche o campo de texto; ele pode usar o serviço de fala configurado
pelo próprio navegador. Identificação biométrica do falante não é realizada nem usada como senha.

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

O botão **Usar microfone** solicita `RECORD_AUDIO` somente após ação explícita, usa o reconhecedor de
fala disponível no Android e coloca a transcrição no campo para revisão antes do envio. A
disponibilidade e eventual uso de rede dependem do serviço de fala instalado no próprio aparelho;
quando indisponível, o texto continua sendo o fallback.

## Cliente Linux

O cliente em [`apps/linux`](apps/linux) usa Flutter/Dart e compartilha o contrato HTTP do núcleo.
No Windows é possível analisar e testar os widgets; o binário Linux e o Flatpak são produzidos em
um runner Linux:

```powershell
cd apps\linux
..\..\.toolchains\flutter\bin\flutter.bat analyze
..\..\.toolchains\flutter\bin\flutter.bat test
```

## Avatar 3D oficial

O avatar em `assets/avatar` é gerado por programação com Blender headless. O arquivo-fonte
`source/LZ_Agent_Master.blend` preserva o rig mecânico de 32 ossos; `models` contém GLB Lite (4.720
triângulos), Standard (15.576) e Pro (33.848). Cada GLB possui 13 clips: Idle 1/2/3, Listening,
Thinking, Speaking, Acting, Needs Approval, Success, Warning, Error, Offline e Private. A prévia
renderizada fica em `references/generated-preview.png`.

`GET/PUT /api/v1/avatar/state` conecta o núcleo ao `AvatarController`. Chat passa por Thinking e
termina em Success, Private ou Error. Cada estado fornece animação, expressão e ícone; redução de
movimento usa `Static`, e desativar o 3D devolve fallback `2d-static`. Regenere os artefatos com:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python scripts\generate-avatar.py
```

O modelo é uma primeira implementação funcional baseada na prancha aprovada, não uma alegação de
asset final de produção. Integração de renderização nos clientes, revisão profissional das animações,
testes em aparelhos e otimização continuam sendo gates.

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

Projetos e lições autorizadas podem ser corrigidos com `PUT /api/v1/projects/{id}` e
`PUT /api/v1/lessons/{id}`. Fontes e artefatos vinculados ao projeto possuem criação, listagem,
edição, busca, exportação e exclusão confirmada em `/api/v1/projects/{id}/sources`,
`/api/v1/sources/{id}`, `/api/v1/projects/{id}/artifacts` e `/api/v1/artifacts/{id}`. O consentimento
da fonte é explícito ou revogado e todas as mudanças entram no Action Ledger.
`GET /api/v1/memory/search?q=...` pesquisa projetos, lições, sugestões, fontes e artefatos, com filtro
opcional por projeto. `GET/PUT /api/v1/memory/retention` consulta ou altera retenção;
`null` preserva a categoria até exclusão explícita. `POST /api/v1/memory/purge` exige a frase
`APAGAR MEMÓRIA EXPIRADA`, remove somente dados vencidos pela política e registra o expurgo.

`POST /api/v1/memory/backup` cria uma cópia SQLite consistente em `data/backups`, executa
`PRAGMA integrity_check` e devolve tamanho e SHA-256. `POST /api/v1/memory/restore` somente aceita
um arquivo local do diretório de backups, exige o hash esperado e a confirmação textual exata
`RESTAURAR MEMÓRIA`, valida integridade/esquema e cria outro backup de segurança antes de substituir
o banco. Backups permanecem locais e fora do Git.

Fluxo de mudança relevante:

```text
analisar → checkpoint → política/aprovação → alterar → diff → testar → registrar → manter ou rollback
```

`POST /api/v1/projects/{id}/checkpoints` captura somente por comandos Git fixos e de leitura o
commit atual, arquivos modificados e o diff antes da mudança. A captura tem timeout e limite de 2 MiB;
ela não executa rollback automaticamente nem aceita argumentos de shell enviados pelo cliente.

Segredos ficam fora do repositório. Copie `.env.example` para `.env` somente quando habilitar um
provedor externo; `.env`, bancos, backups, caches, certificados e ambientes virtuais são ignorados.

## Plugins

Cada plugin possui ID, versão, descrição, comandos, permissões e entrypoint local. O registro rejeita
manifestos incompletos, IDs inválidos e permissões/comandos duplicados. Instalação não concede
permissão nem execução. Habilitação e grants são persistidos separadamente, exigem confirmação para
concessão e rejeitam capacidades não declaradas no manifesto. Os pacotes iniciais são Produtividade,
Desenvolvedor, Mídia e Blender.

`POST /api/v1/plugins/{id}/execute` exige aprovação, plugin habilitado, integridade SHA-256 e todas as
permissões declaradas concedidas. `GET /api/v1/plugins/sandbox/status` mostra a proteção efetiva. No
Linux, o runner exige Bubblewrap e cria namespaces separados, remove capabilities, bloqueia rede e
expõe somente runtime e entrypoint como leitura, além de `/tmp` efêmero. Instale com o gerenciador da
distribuição, por exemplo `sudo apt install bubblewrap` no Ubuntu/Debian.

No Windows, a execução fica bloqueada com HTTP 503 até o helper LPAC/AppContainer assinado estar
instalado. Não existe fallback para subprocesso comum. Entrada/saída JSON, timeout e limites de
tamanho continuam obrigatórios; sucesso, falha e bloqueio entram no Action Ledger. Os plugins
incluídos são pequenos, sem imports externos, e seus hashes fazem parte dos manifestos.

Projetos Unity, Unreal Engine e Godot serão produzidos por código e
automação reproduzível: fontes, cenas textuais, configurações e manifests versionados, com builds
headless/batch por CLI e nenhuma etapa manual oculta em editor. Consulte
[`docs/ENGINE_CODE_WORKFLOW.md`](docs/ENGINE_CODE_WORKFLOW.md).

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

## Sincronização segura com GitHub

A tarefa VS Code **LZ: sincronização segura automática com GitHub** inicia ao abrir a pasta (depois
que o VS Code autorizar tarefas automáticas). A cada mudança ela considera apenas arquivos não
ignorados, bloqueia nomes/conteúdo com aparência de segredo e arquivos acima de 25 MB, executa Ruff,
pytest e validação JavaScript, então cria commit e envia a branch atual. Execute uma vez sem vigiar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\safe-github-sync.ps1
```

`.env`, bancos, backups, certificados, toolchains, caches e builds continuam deliberadamente fora do
GitHub. Releases são produzidas por tags e CI; não se usa a pasta `build` local como fonte de release.

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

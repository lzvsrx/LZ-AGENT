# LZ Agent

Agente pessoal multimodal, acessível, extensível e orientado a tarefas para Windows, Android e
Linux. Este monorepo implementa a especificação do **Documento Mestre Completo 2026** com uma
fonte de verdade comum para configurações, memória, permissões e estados.

## Executar o núcleo local

Requer Python 3.14.7.

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m lz_agent.main
```

Abra <http://127.0.0.1:8765>. A API interativa fica em `/docs` e o diagnóstico em
`/api/v1/system/health`.

Nenhuma chave é incluída no repositório. Copie `.env.example` para `.env` apenas quando habilitar
um provedor externo. Sem chave, o agente permanece funcional em modo local demonstrativo.

## Estrutura

- `core/agent`: orquestração, políticas, contratos e servidor local.
- `data`: migrações SQLite, backups locais ignorados e esquemas.
- `apps`: clientes de plataforma.
- `plugins`: capacidades isoladas por manifesto e permissão.
- `assets`: marca, avatar e arquivo visual histórico.
- `docs`: arquitetura, segurança, acessibilidade e matriz de suporte.
- `versions`: baseline técnico reproduzível.

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) e [SECURITY.md](SECURITY.md) antes de contribuir.


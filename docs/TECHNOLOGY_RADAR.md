# Radar tecnológico do LZ Agent

Este radar complementa `versions/technology-baseline.json`. Versão nova é candidata, não aprovação:
só entra no baseline depois de notas oficiais, build, testes, acessibilidade, desempenho, migração de
dados e rollback. O repositório e a CI são a fonte de verdade.

| Anel | Uso | Tecnologias atuais |
|---|---|---|
| Adotar | base implementada e verificada pela CI | Python/FastAPI/SQLite; Kotlin/Compose; C#/.NET/WinUI 3; Flutter/Dart; Blender Python/glTF |
| Experimentar | protótipo isolado antes de integrar | Flatpak/Portals; cofre nativo por SO; PostgreSQL opcional; STT/TTS locais; renderer GLB nos clientes |
| Avaliar | pesquisa com threat model e critérios de saída | embeddings locais; GPU/NPU; sincronização E2EE; sandbox multiplataforma de plugins |
| Evitar | incompatível com a arquitetura vigente | Docker como requisito do produto; permissões irrestritas; atualização automática sem testes; retenção secreta; dependência obrigatória de um provedor de IA |

## Processo de promoção

1. Registrar candidato, versão, fonte oficial, licença e motivo.
2. Reproduzir instalação em ambiente limpo e executar todas as plataformas afetadas.
3. Medir regressões de CPU, RAM, bateria, latência e tamanho quando aplicável.
4. Validar migração, restauração, segurança, privacidade e acessibilidade.
5. Atualizar baseline, proveniência, documentação e changelog no mesmo pull request.

Dependabot apenas abre propostas. Nenhuma proposta promove uma dependência por conta própria.

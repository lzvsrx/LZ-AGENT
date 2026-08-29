# Arquitetura

O LZ Agent separa apresentação, orquestração, provedores, políticas, ferramentas e memória. Os
clientes de plataforma consomem contratos versionados em `shared/schemas`; nenhum cliente acessa
diretamente um provedor de IA nem ignora a camada de autorização.

Fluxo de ação: entrada acessível → planejamento → decisão de política → registro da intenção →
aprovação quando exigida → execução isolada → resultado/diff/testes → registro auditável → lição
somente quando autorizada. Mudanças relevantes exigem checkpoint e oferecem rollback.

SQLite é o padrão local. PostgreSQL é uma opção futura de sincronização autenticada e criptografada,
não uma dependência para funcionamento. Docker/containers não fazem parte da arquitetura exigida.


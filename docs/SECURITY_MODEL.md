# Segurança, privacidade e retenção

## Fronteira de plugins

Plugins empacotados exigem comando declarado, grants conferidos, aprovação explícita, SHA-256 válido,
entrada/saída JSON limitada e timeout. O hash é verificado ao descobrir o plugin e novamente antes de
executá-lo. Alteração de um byte invalida o pacote. Toda tentativa concluída ou bloqueada entra no
Action Ledger.

No Linux, apenas Bubblewrap é aceito: novo namespace de usuário/processo/rede/montagem, capabilities
removidas, rede ausente, runtime somente leitura, somente o entrypoint montado e `/tmp` efêmero. No
Windows, subprocesso comum, Job Object e low-integrity isoladamente não satisfazem esta política. A
execução permanece bloqueada até um helper LPAC/AppContainer assinado conceder somente os recursos
declarados. Outros sistemas também falham fechados. Plugins externos permanecem desabilitados até
assinatura, revisão de origem e sandbox compatível.

Referências: [Bubblewrap](https://github.com/containers/bubblewrap) e
[AppContainer/LPAC](https://learn.microsoft.com/windows/win32/secauthz/appcontainer-isolation).

- Privilégio mínimo por plugin e capacidade.
- Consentimento explícito para exclusões, publicação, mensagens, compras e dados sensíveis.
- Segredos somente no cofre da plataforma ou em variáveis locais ignoradas.
- Registrar o que o agente faz, não tudo que o usuário vê, fala ou possui.
- Sessão privada não persiste conteúdo; toda memória pode ser pesquisada, exportada e apagada.
- Sincronização permanece desativada por padrão.
- Atualizações e releases devem ser assinadas; dependências passam por auditoria.

Relate vulnerabilidades de forma privada conforme `SECURITY.md`.

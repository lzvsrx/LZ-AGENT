# Segurança, privacidade e retenção

## Fronteira de plugins

Plugins empacotados executam fora do processo da API, com comando declarado, grants conferidos,
aprovação explícita, entrada/saída JSON limitadas, ambiente mínimo, diretório temporário e timeout.
Toda tentativa concluída entra no Action Ledger. Essa contenção reduz falhas acidentais, mas ainda
não impede por si só que código Python malicioso acesse recursos concedidos ao usuário do sistema.
Consequentemente, código de terceiros permanece não confiável e desabilitado até receber assinatura,
revisão e sandbox nativa (AppContainer no Windows e seccomp/Flatpak no Linux; isolamento Android no
aplicativo correspondente).

- Privilégio mínimo por plugin e capacidade.
- Consentimento explícito para exclusões, publicação, mensagens, compras e dados sensíveis.
- Segredos somente no cofre da plataforma ou em variáveis locais ignoradas.
- Registrar o que o agente faz, não tudo que o usuário vê, fala ou possui.
- Sessão privada não persiste conteúdo; toda memória pode ser pesquisada, exportada e apagada.
- Sincronização permanece desativada por padrão.
- Atualizações e releases devem ser assinadas; dependências passam por auditoria.

Relate vulnerabilidades de forma privada conforme `SECURITY.md`.

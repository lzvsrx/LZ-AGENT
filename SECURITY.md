# Política de segurança

## Autenticação local

- senhas são derivadas com Argon2id e nunca registradas em logs;
- tokens aleatórios são armazenados apenas como hash, expiram e podem ser revogados;
- respostas de cadastro nunca devolvem hash ou senha;
- após o primeiro cadastro, rotas pessoais exigem sessão e novas contas exigem autenticação;
- voz não é credencial biométrica e o microfone exige ativação explícita;
- o nome do dispositivo é omitido da detecção padrão.

Não abra uma issue pública com chaves, dados pessoais ou detalhes exploráveis. Use o canal privado
de Security Advisories do GitHub. Inclua versão, impacto, reprodução mínima e mitigação conhecida.
O projeto não promete suporte profissional para saúde, direito, segurança ou finanças.

# Processo de release

1. Confirmar inventário de dependências, licenças, segredos e dados pessoais.
2. Executar lint, testes, migrações, acessibilidade e diagnóstico nos perfis suportados.
3. Atualizar changelog, baseline, matriz de suporte, matriz jurídica e problemas conhecidos.
4. Revisar diff e criar tag assinada `vMAJOR.MINOR.PATCH`.
5. O GitHub Actions gera wheel, arquivo-fonte e notas da release a partir da tag.
6. Binários nativos só entram quando seus builds e assinaturas forem reproduzíveis e testados.

Uma tag não transforma protótipo em suporte de produção. Cada release declara exatamente os clientes,
arquiteturas, países e recursos validados.


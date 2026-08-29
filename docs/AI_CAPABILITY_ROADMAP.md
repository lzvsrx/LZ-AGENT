# Matriz de capacidades da IA própria

Esta matriz transforma “fazer o que outras IAs fazem” em requisitos testáveis. Ela não autoriza
copiar código, pesos, dados, prompts privados, marcas ou comportamento proprietário. O LZ Agent deve
implementar capacidades equivalentes com componentes próprios, dados licenciados e avaliação
independente.

| Capacidade | Estado atual | Conclusão verificável |
|---|---|---|
| Conversa multilíngue | núcleo nativo inicial | modelo próprio responde com qualidade medida por locale |
| Raciocínio e planejamento | contratos iniciais | planos, dependências, limites e replanejamento avaliados |
| Programação | checkpoints Git | edição multi-arquivo, terminal isolado, testes, diff e rollback |
| Pesquisa web | parcial funcional | múltiplas fontes, citações, datas, cache, robots e defesa contra injeção |
| Arquivos e conhecimento | inspeção parcial | extração, OCR, busca semântica, citações e política de retenção |
| Visão | metadados apenas | descrição, OCR e análise visual avaliados e consentidos |
| Voz | microfone/ditado web | STT/TTS local multilíngue, interrupção e latência avaliados |
| Imagem e vídeo | planejado | geração/edição com proveniência, licença, segurança e marcação |
| Memória | parcial funcional | preferências/fontes editáveis, busca, retenção e exclusão por usuário |
| Ferramentas/plugins | grants parciais | runner isolado, schema I/O, timeout, cancelamento e auditoria |
| Computador e dispositivos | detecção parcial | ações acessíveis, allowlist, confirmação e captura de resultado |
| Tarefas longas/agendadas | planejado | fila persistente, progresso, pausa, retomada e notificações |
| Colaboração entre agentes | planejado | delegação limitada, orçamento, proveniência e síntese verificável |
| Personalização | inicial | perfis por usuário, portabilidade e controles de privacidade |
| Segurança | parcial | threat model, red team, prompt injection, secrets, sandbox e incidentes |
| Avaliações | testes iniciais | suites de qualidade, segurança, regressão, idioma, custo e desempenho |

## Regra para pesos próprios

Um modelo só pode ser chamado de “IA generativa própria do LZ Agent” quando houver, no mínimo:

1. arquitetura e pipeline de treinamento versionados;
2. corpus com proveniência e licença compatível, remoção de dados pessoais e política de opt-out;
3. checkpoints/pesos produzidos pelo projeto, hashes e assinatura;
4. avaliações públicas de qualidade, segurança, vieses, memorização e idiomas;
5. model card, limites conhecidos, requisitos de hardware e plano de atualização/rollback.

Até esse gate, `native-core-v1` é corretamente descrito como núcleo determinístico de orquestração,
não como um grande modelo de linguagem. Essa distinção impede propaganda enganosa e permite evoluir
o produto por evidência.

## Ordem de entrega

1. Fechar autenticação/autorização e isolamento de ferramentas.
2. Conectar pesquisa com citações e proteção contra conteúdo hostil.
3. Criar runtime de tarefas de código com checkpoint/teste/rollback.
4. Implementar STT/TTS e conhecimento local.
5. Preparar dados, tokenizer, treino, avaliações e distribuição dos pesos próprios.
6. Só então ampliar multimodalidade, colaboração e automação autônoma.

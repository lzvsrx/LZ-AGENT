# Matriz jurídica e regulatória

Revisão de pesquisa: **29/08/2026**. Este documento é um inventário de engenharia, não um parecer
jurídico. Nenhum software pode garantir conformidade com “todas as leis do mundo” nem risco jurídico
zero: jurisdição, público, finalidade, setor, dados e modelo comercial mudam as obrigações. Uma
revisão por advogado habilitado no país e no setor é um gate obrigatório antes de cada lançamento.

## Regras globais incorporadas ao produto

1. Inventário de dados, finalidade, base legal, retenção, destinatários, país e responsável por fluxo.
2. Privacidade e segurança desde a concepção; minimização; configuração protetiva por padrão.
3. Consentimento granular quando for a base aplicável, revogável com a mesma facilidade.
4. Painel para acesso, correção, portabilidade/exportação, oposição e eliminação.
5. Avaliação de impacto antes de biometria, vigilância, crianças, dados sensíveis, grande escala ou
   decisões com efeito jurídico/significativo.
6. Intervenção humana real, contestação e explicação para decisões de impacto; o LZ Agent não toma
   sozinho decisões médicas, jurídicas, trabalhistas, creditícias, educacionais ou governamentais.
7. Aviso inequívoco de que o usuário interage com IA; rotulagem e metadados para conteúdo sintético.
8. Proibição de manipulação enganosa, social scoring, exploração de vulnerabilidades, discriminação,
   deepfake íntimo sem consentimento e material de abuso sexual infantil.
9. Segurança proporcional ao risco, plano de incidentes, registro, comunicação legal e cadeia de
   fornecedores/suboperadores.
10. Controle de transferência internacional, localização e contrato antes de enviar dados à nuvem.
11. Acessibilidade WCAG 2.2 AA e APIs nativas; alternativa humana/acessível para funções essenciais.
12. Respeito a direitos autorais, marcas, imagem, voz, personalidade, licenças de dados/modelos e
   atribuições; nenhuma coleta indiscriminada para treinamento.

## Brasil — federal

| Norma/autoridade | Aplicação ao LZ Agent | Gate técnico e operacional |
|---|---|---|
| Constituição Federal, direitos fundamentais e proteção de dados | Privacidade, igualdade, devido processo, honra, imagem e não discriminação | revisão de direitos fundamentais e mecanismo de contestação |
| LGPD, Lei 13.709/2018 | Dados pessoais, sensíveis, biométricos, perfis, crianças, segurança, direitos, decisões automatizadas e transferências | registro de operações, base legal por finalidade, RIPD, encarregado/canal, direitos e retenção |
| Marco Civil, Lei 12.965/2014, e regulamentos | Privacidade, registros, segurança e aplicações de internet | política de logs mínima, ordens legais validadas e exclusão ao fim da relação |
| CDC, Lei 8.078/1990 | Oferta clara, segurança, qualidade, responsabilidade, publicidade e contratos | informar limites/erros/custos, suporte, termos legíveis e proibir dark patterns |
| ECA + ECA Digital, Lei 15.211/2025 e Decreto 12.880/2026 | Serviço de acesso provável por menores, melhor interesse, segurança e aferição de idade | modo infantil protetivo, verificação proporcional, controles parentais e proibição de perfilamento comercial por padrão |
| LBI, Lei 13.146/2015, e normas de acessibilidade | Não discriminação e acessibilidade de serviços digitais | auditoria WCAG 2.2 AA + testes assistivos por plataforma |
| Direitos autorais, Lei 9.610/1998; software, Lei 9.609/1998; propriedade industrial, Lei 9.279/1996 | Código, datasets, mídia, voz, marca, plugins e saídas | SBOM/licenças/proveniência, autorização de imagem/voz e processo de remoção |
| Código Civil e leis penais/cibernéticas | Responsabilidade, personalidade, fraude, invasão e conteúdo ilícito | allowlist, consentimento, logs seguros e bloqueio de ações criminosas |
| Regras setoriais | Saúde, finanças, crédito, trabalho, educação, telecom e governo têm normas próprias | módulo desativado até análise jurídica setorial e revisão humana qualificada |

Fontes oficiais: [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm),
[Marco Civil](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm),
[ECA Digital](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15211.htm),
[orientações e normas da ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/documentos-tecnicos-orientativos),
[incidentes de segurança](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis).

### Inteligência artificial no Brasil

Em 29/08/2026, o PL 2.338/2023 ainda aparece em tramitação na Câmara; ele não deve ser descrito como
lei vigente. O produto deve acompanhar a [ficha oficial de tramitação](https://www.camara.leg.br/proposicoesWeb/fichadetramitacao/?idProposicao=2487262)
e aplicar desde já controles de risco compatíveis, sem confundi-los com obrigação legal promulgada.

## Estado de São Paulo e municípios

Para uma empresa privada de software, LGPD e normas federais gerais continuam centrais. Leis
estaduais/municipais variam conforme contratação pública, tributação, consumidor local, educação,
saúde, biometria, vigilância e uso pelo governo. Antes de operar ou contratar em São Paulo, o release
deve passar por busca atualizada na ALESP, Diário Oficial e município relevante. Projetos de lei, como
o PL paulista 363/2026 sobre IA na administração estadual, não são tratados como lei vigente.

## União Europeia/EEE

- GDPR: base legal, transparência, minimização, direitos, DPIA, privacy by design/default,
  transferências e salvaguardas para decisões automatizadas.
- AI Act, Regulamento (UE) 2024/1689: práticas proibidas, alfabetização em IA, classificação de risco,
  documentação, supervisão, transparência de chatbot e conteúdo sintético. Em 02/08/2026 passaram a
  valer requisitos gerais e de transparência; prazos de alto risco seguem cronograma específico.
- ePrivacy/cookies, Digital Services Act quando houver intermediação, European Accessibility Act e
  legislação de consumidor, produto, cibersegurança, copyright e bases de dados conforme o serviço.

Fontes: [texto oficial do AI Act](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689),
[cronograma da Comissão](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai),
[Artigo 50/transparência](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act).

## Reino Unido

UK GDPR e Data Protection Act exigem licitude, direitos, avaliação de risco e salvaguardas para
decisões automatizadas; PECR cobre comunicações/cookies e o Children's Code aplica design apropriado
à idade. Conferir atualizações posteriores ao Data (Use and Access) Act.

Fonte: [ICO — AI e proteção de dados](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/).

## Estados Unidos

Não existe uma única lei federal geral equivalente à LGPD. O gate deve avaliar FTC Act (práticas
injustas/enganosas), COPPA, direitos civis/antidiscriminação, acessibilidade, copyright, biometria,
saúde, crédito, emprego, comunicações e leis estaduais. O produto começa com Califórnia (CCPA/CPRA e
regras de ADMT), Colorado, Connecticut, Virginia, Texas, Utah e demais estados com leis abrangentes;
Illinois BIPA e normas locais exigem atenção especial para biometria. NIST AI RMF é voluntário, mas
será o framework técnico mínimo.

Fontes: [California CCPA](https://oag.ca.gov/privacy/ccpa/regs),
[aplicação das leis da Califórnia à IA](https://oag.ca.gov/system/files/attachments/press-docs/Legal%20Advisory%20-%20Application%20of%20Existing%20CA%20Laws%20to%20Artificial%20Intelligence.pdf),
[NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework).

## Outros mercados que exigem gate antes do lançamento

| Mercado | Baseline a confirmar com advogado local |
|---|---|
| Canadá | PIPEDA e leis provinciais; consentimento significativo, finalidade apropriada e proteção de menores |
| Austrália | Privacy Act/APPs, Online Safety e regras de consumidor |
| Japão | APPI, diretrizes da PPC, transferências e cautelas específicas para IA generativa |
| Índia | DPDP Act 2023 e DPDP Rules 2025, consentimento/aviso, direitos, menores e implantação faseada |
| China | PIPL, Data Security Law, Cybersecurity Law e regras de algoritmo/deep synthesis/IA generativa; avaliação/localização quando aplicável |
| Coreia do Sul | PIPA e AI Basic Act/regulamentos vigentes |
| Singapura | PDPA e Model AI Governance Framework |
| África do Sul | POPIA; responsável, finalidade, segurança, direitos e transferências |
| América Latina | Leis nacionais (Argentina, Chile, Colômbia, México, Uruguai etc.); bases legais, registro/autoridade e transferências variam |
| Oriente Médio | Leis federais e de zonas/país (EAU, Arábia Saudita, Israel etc.); localização e dados sensíveis variam |

Fontes iniciais oficiais: [Canadá — investigação de IA generativa](https://www.priv.gc.ca/en/opc-actions-and-decisions/investigations/investigations-into-businesses/2026/pipeda-2026-002/),
[Japão — APPI](https://www.ppc.go.jp/en/legal/), [Índia — DPDP Act](https://www.meity.gov.in/static/uploads/2024/02/Digital-Personal-Data-Protection-Act-2023.pdf).

## Gate obrigatório de release por território

O release só pode marcar um país como suportado quando `docs/legal/jurisdictions/<codigo>.json`
contiver: versão/data das normas; entidade e papéis; fluxos/dados; base legal; menores; biometria;
decisão automatizada; transferências; retenção; acessibilidade; consumidor; propriedade intelectual;
incidentes; contato/DPO; testes; parecer e responsável que aprovou. Sem isso, o país permanece
“não avaliado” e serviços remotos/alto risco ficam desativados.


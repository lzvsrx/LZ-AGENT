# Originalidade, dependências e proveniência

O núcleo do LZ Agent é desenvolvido neste repositório. Nenhum código, peso, prompt privado ou
segredo comercial de ChatGPT, Codex ou outro produto deve ser copiado, descompilado ou renomeado como
se fosse próprio.

## Classificação obrigatória

- `original`: código criado para o LZ Agent e mantido no repositório;
- `dependency`: biblioteca/runtime externo usado pela interface pública e conforme sua licença;
- `standard`: protocolo ou formato público implementado pelo projeto;
- `asset`: imagem, voz, modelo ou dataset com autor, fonte e licença registrados;
- `generated`: saída criada por ferramenta, acompanhada de fonte, ferramenta e revisão humana.

O manifesto `versions/component-provenance.json` é a lista canônica inicial. Uma dependência externa
não deixa o agente menos próprio; ocultar sua origem ou licença, sim. Código gerado só pode entrar
após revisão, testes e verificação de licença. Pesos de IA somente podem ser chamados de próprios
quando cumprirem todos os gates de `AI_CAPABILITY_ROADMAP.md`.

# Idiomas, regiões, texto e áudio

O objetivo é aceitar qualquer locale BCP 47 e expandir cobertura para todas as línguas e variantes
regionais para as quais exista tecnologia utilizável. Cobertura não equivale a qualidade verificada:
um idioma só entra na lista de suporte da release depois de revisão por falante nativo, testes de
texto, plural, datas, números, layout, acessibilidade, STT e TTS.

## Regras obrigatórias

- Preservar variantes como `pt-BR`, `pt-PT`, `es-MX`, `es-ES`, `zh-Hans-CN` e `zh-Hant-TW`.
- Nunca traduzir nomes, preferências ou conteúdo do usuário sem autorização.
- Detectar idioma, mas permitir seleção manual e manter a escolha do usuário como autoridade final.
- Usar Unicode, segmentação e fontes com cobertura adequada; não presumir alfabeto latino.
- Suportar escrita LTR/RTL, espelhamento de layout e entrada bidirecional.
- Formatar datas, números, moedas, unidades e plural conforme locale; não concatenar frases.
- Usar fallback `idioma-região → idioma → inglês`, informando quando o fallback ocorrer.
- Enumerar vozes do sistema/provedor em tempo de execução. Nunca escolher voz de outro idioma em
  silêncio nem afirmar STT/TTS onde a tecnologia não estiver disponível.
- Para línguas de sinais, AAC e pessoas sem fala, oferecer texto, símbolos, legendas e interfaces
  visuais; TTS não é substituto para língua de sinais.
- Áudio enviado à nuvem exige consentimento específico, indicador de gravação, retenção mínima e
  informação do país/provedor. O padrão preferido é processamento local quando viável.
- Vozes clonadas exigem consentimento verificável e revogável; impersonação e fraude são proibidas.

Os catálogos começam com `pt-BR` e `en` como referências revisáveis. Traduções futuras devem ser
arquivos separados, testáveis e atribuídos; tradução automática pode gerar rascunho, nunca aprovação.


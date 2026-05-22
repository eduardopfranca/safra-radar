# DECISIONS_LOG — Safra Radar
**Versao | 21/05/2026 | Append-only**

> Registro de decisoes arquiteturais, padroes de trabalho e licoes aprendidas.
> Consultar antes de propor mudancas estruturais. Toda decisao listada aqui deve ser respeitada ate ser explicitamente revisada via novo registro datado.

---

## Decisoes Arquiteturais

### D01 — Safra Radar e modulo do Safra Segura (Madcap)
**Data:** 21/05/2026
**Decisao:** o Safra Radar e um modulo do Safra Segura, produto da Madcap.
**Impacto:** Safra Radar e projeto independente; futuramente sera integrado como modulo do Safra Segura.

### D02 — Eduardo administra todo o stack tecnico
**Data:** 21/05/2026
**Decisao:** Eduardo administra repositorio, Supabase, Render, Vercel, Lovable, dominio e qualquer infraestrutura tecnica.
**Impacto:** Toda configuracao manual (env vars, SQL, Edge Functions) e responsabilidade de Eduardo.

### D03 — MVP com atualizacao pull-based, sem cronjob
**Data:** 21/05/2026
**Decisao:** no MVP nao havera cronjob nem coleta automatica em background. Cada bloco da tela tem botao "atualizar" proprio + badge de desatualizacao com timestamp.
**Justificativa:** simplifica drasticamente a infraestrutura inicial. Permite validar a viabilidade de cada fonte de dado antes de investir em scheduling. Evita custo de execucao continua durante validacao do produto.
**Impacto:** o primeiro usuario que abrir cada bloco do dia paga o custo da chamada externa. Aceitavel no MVP. Migrara para cronjob/cache central quando volume justificar.
**Threshold de desatualizacao por bloco:** definir caso a caso (ex: precos 15min, calendario 24h, ENSO 7 dias).

### D04 — Safra Radar nunca recomenda venda
**Data:** 21/05/2026
**Decisao:** o produto nunca produzira recomendacao de venda ("venda X% agora", "trave isso"). Entrega dado, contexto historico e visual claro. Decisao e do produtor.
**Justificativa:** filosofica (respeito a autonomia do produtor) e juridica (sem responsabilidade por orientacao financeira a terceiros). Posicionamento do produto se baseia em servir como **catalisador de procura pela mesa**, nao como advisor.
**Impacto:** qualquer feature que se aproxime de recomendacao automatica precisa de aval explicito de Eduardo em DECISIONS_LOG antes de ser implementada. Mesmo em fases futuras.

### D05 — Linguagem do produto e o portugues do produtor
**Data:** 21/05/2026
**Decisao:** todo texto exibido ao usuario final usa portugues coloquial do produtor brasileiro: "saca", "trava", "premio porto", "alta/baixa". Termos tecnicos (basis, hedge, MTM, bushel) so com glossario inline ou tooltip.
**Justificativa:** publico alvo (medio produtor 500–3.000 ha) nao tem letramento em mercado financeiro. Traducao e diferencial central do produto.
**Impacto:** Glossary.md sera mantido como fonte de verdade dos termos publicos. Conteudo editorial pos-evento segue a mesma regra.

---

## Padroes de trabalho

### P01 — Documentacao objetiva
**Data:** 21/05/2026

### P02 — Uma etapa por vez, com confirmacao
**Data:** 21/05/2026
**Padrao:** Claude nunca empilha multiplas execucoes em um unico prompt. Cada migration SQL, cada arquivo de codigo, cada prompt para agente executor e enviado individualmente, com confirmacao de Eduardo antes de avancar.
**Justificativa:** Evita erros caros, mantem controle.

### P03 — Nunca trabalhar em arquivo sem conteudo completo
**Data:** 21/05/2026
**Padrao:** Claude nunca propoe edicao em arquivo sem que Eduardo cole o conteudo atual completo no chat. Nao assumir o que existe.
**Justificativa:** drift entre o que Claude lembra e a realidade no repo gera bugs silenciosos.

### P04 — Teste de fronteira antes de cada prompt
**Data:** 21/05/2026
**Padrao:** antes de redigir qualquer prompt para Claude Code, Lovable ou Supabase Dashboard, aplicar o teste: "esse prompt toca apenas uma camada?". Se nao, decompor.

### P05 — Git push e responsabilidade de Eduardo
**Data:** 21/05/2026
**Padrao:** Claude Code prepara commits, mas o push e feito manualmente por Eduardo (`git push origin master:main`). Documentacao .md atualizada via Claude Code sempre com instrucao explicita "nao commitar, nao pushar".
**Justificativa:** controle de versao consciente. Eduardo decide quando e o que sobe.

### P06 — Citar fonte e timestamp em todo dado externo
**Data:** 21/05/2026
**Padrao:** todo endpoint que retorna dado externo (preco, evento, indicador) inclui no payload: `source` (string), `source_url` (string, opcional), `fetched_at` (ISO 8601), `source_timestamp` (ISO 8601 quando disponivel). Frontend exibe ao usuario.
**Justificativa:** confiabilidade da fonte e parte central da promessa do produto. Usuario precisa saber de onde veio e quando.

---

## Licoes aprendidas

(Vazio no inicio. Sera preenchido conforme bugs e correcoes acontecerem.)

---

*Fim do documento — DECISIONS_LOG.md*

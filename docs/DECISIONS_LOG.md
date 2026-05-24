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

### D06 — Projeto Supabase dedicado
**Data:** 21/05/2026
**Decisao:** projeto Supabase criado especificamente para o Safra Radar — ref ID `lacgthfskkcrhmfahjzj`, regiao Sao Paulo (sa-east-1), plano Free.
**Justificativa:** D01 estabelece o Safra Radar como projeto independente. Projeto Supabase compartilhado violaria a independencia.
**Impacto:** todas as Edge Functions, SQL migrations e secrets vivem nesse projeto. Quando o Safra Radar for integrado ao Safra Segura, decisao de migracao ou bridge sera tomada com base no estado real do produto.

### D07 — Conta Render em plano Free durante o MVP
**Data:** 22/05/2026
**Decisao:** backend hospedado no Render em plano Free durante validacao do produto. Cold start (~30s no primeiro request apos 15min de inatividade) e aceito como parte do MVP.
**Justificativa:** otimizar custo durante validacao. Pagar plano antes de ter cliente seria gastar por boas praticas teoricas.
**Impacto:** primeiro usuario do dia paga o custo de UX do cold start. Aceitavel ate volume justificar upgrade. Quando primeiro cliente pagante existir, avaliar Starter (~7 USD/mes) ou similar.

### D08 — Branch principal `main`
**Data:** 22/05/2026
**Decisao:** branch principal do repositorio Git e `main`, nao `master`. Padrao adotado desde a criacao do repo via `git init -b main`.
**Justificativa:** convencao moderna do GitHub e da industria desde 2020. Reduz friccao com tooling e documentacao externa.
**Impacto:** comando de push de Eduardo passa a ser `git push origin main`. P05 atualizado em 23/05/2026.

### D09 — Claude Code como agente executor de codigo
**Data:** 22/05/2026
**Decisao:** Claude Code (CLI da Anthropic, instalado via `npm install -g @anthropic-ai/claude-code`) e o agente executor padrao para trabalho de codigo e arquivos do repositorio Python. Versao no momento da adocao: 2.1.148.
**Justificativa:** integra com Claude Pro de Eduardo (sem custo adicional), opera direto no filesystem local (sem sandbox intermediario), suporta sessao interativa e prompt nao-interativo (`Get-Content prompt.txt | claude`).
**Impacto:** Claude Code edita arquivos diretamente em `C:\Users\eduar\code\safra-radar`. Nunca executa comandos git (ver P05). Pode ser usado via CLI no PowerShell ou via extensao oficial da Anthropic no VS Code. GitHub Copilot NAO e Claude Code (licao L06).

### D10 — Probes-first para fontes novas
**Data:** 22/05/2026
**Decisao:** todo provedor de dado externo novo passa por probe de descoberta antes da implementacao do client. O probe nao chuta — lista o universo real (atributos, commodities, paises, statisticat categories) usando os endpoints meta da propria API quando disponiveis (`/commodityAttributes`, `/commodities`, `/countries`, etc.).
**Justificativa:** descobrimos na sessao de 22/05/2026 que chutar IDs/categorias gera bugs silenciosos dificeis de detectar (atributo mapeado com ID errado passa em todos os testes mas retorna dado incorreto).
**Impacto:** todo novo client em `connections/` deve ter um `scripts/probe_*.py` correspondente executado e revisado antes da implementacao.

### D11 — Camada de comparacao fica em engines, nao em clients
**Data:** 22/05/2026
**Decisao:** a SPEC ja estabelece que connections sao I/O puro, mas isso foi explicitamente confirmado em decisao: calculos de variacao (YoY, WoW, vs. media 5 anos) vivem em `engines/`, com atomicos reutilizaveis em `utils.py`. Clients retornam dado bruto P06-wrapped e nunca fazem aritmetica sobre os valores.
**Justificativa:** separacao de responsabilidades — um bug de calculo nao contamina a camada de coleta e vice-versa.
**Impacto:** engines nao foram criados ainda — serao criados quando houver multiplos consumidores da logica de comparacao. Por ora os blocos `if __name__ == "__main__":` dos clients importam `utils.py` diretamente para simular o produto final durante desenvolvimento.

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
**Padrao:** Claude Code prepara commits, mas o push e feito manualmente por Eduardo (`git push origin main`). Documentacao .md atualizada via Claude Code sempre com instrucao explicita "nao commitar, nao pushar".
**Justificativa:** controle de versao consciente. Eduardo decide quando e o que sobe.

### P06 — Citar fonte e timestamp em todo dado externo
**Data:** 21/05/2026
**Padrao:** todo endpoint que retorna dado externo (preco, evento, indicador) inclui no payload: `source` (string), `source_url` (string, opcional), `fetched_at` (ISO 8601), `source_timestamp` (ISO 8601 quando disponivel). Frontend exibe ao usuario.
**Justificativa:** confiabilidade da fonte e parte central da promessa do produto. Usuario precisa saber de onde veio e quando.

---

## Licoes aprendidas

### L01 — Agentes executores saem de escopo sem guardrails explicitos
**Data:** 22/05/2026
Na primeira passada da Fase 0, o Claude Code: (a) inventou o arquivo `CLAUDE.md` que nao estava no escopo, (b) pre-criou subpastas `api/routers/` e `api/schemas/` antecipando a Fase 2, (c) ignorou a instrucao de rename `docs/README.md` para `docs/OVERVIEW.md`. Licao: prompts enxutos em "como executar", mas explicitos em "o que nao fazer" e em renames. Confiar no agente nao exclui guardrails de escopo.

### L02 — Validacao humana e o checkpoint critico da cadeia
**Data:** 22/05/2026
Cada um dos desvios da L01 passaria silenciosamente se a validacao manual nao comparasse o output contra o prompt original. Validar contra o que o agente diz que fez (summary) NAO substitui validar contra o que foi pedido. Sem a validacao manual antes do `git push`, a Fase 0 teria ido para o GitHub com 3 desvios.

### L03 — Git e sempre responsabilidade humana, mesmo quando o agente oferece executar
**Data:** 22/05/2026
Claude Code oferece rodar `git init`, `git add`, `git commit` quando termina trabalho. Recusar a oferta faz parte do trabalho — P05 nao e teorico. Mesma logica se aplica a qualquer outro agente (Cursor, Cline, Copilot). Push e commit ficam manual, sempre.

### L04 — Endpoints meta de APIs governamentais economizam horas
**Data:** 22/05/2026
APIs como USDA FAS PSD expoe endpoints especificos para listar atributos (`/commodityAttributes`), commodities (`/commodities`), paises (`/countries`). Sempre buscar esses endpoints meta antes de redigir probe de descoberta — eles sao a fonte canonica e evitam adivinhacao. Buscar primeiro na documentacao oficial; se nao houver, no Swagger/OpenAPI; se nem isso, em SDKs comunitarios.

### L05 — Prompt grande no PowerShell trunca silenciosamente
**Data:** 22/05/2026
O PowerShell tem buffer limitado para colagem direta. Prompts longos colados sao silenciosamente cortados — o agente recebe metade e executa so essa metade. Sintoma: agente cumpre so uma fracao das tarefas listadas sem reportar erro. Solucao: salvar prompt em arquivo e usar `Get-Content prompt.txt | claude`, ou usar a UI integrada do VS Code (Claude Code extension) que nao tem esse problema.

### L06 — Agentes diferentes tem capacidades muito diferentes
**Data:** 22/05/2026
GitHub Copilot e Claude Code coexistem no VS Code e parecem intercambiaveis na UI, mas modelos e limites sao distintos. Copilot Raptor mini falhou com 408 em prompt medio que Claude Code Sonnet executou sem problema. Identificar a extensao correta antes de mandar trabalho tecnico — nao assumir que qualquer assistente de codigo serve para qualquer tarefa.

### L07 — Probes devem cobrir todas as statisticcat_desc consumidas
**Data:** 23/05/2026
O probe NASS original cobriu STOCKS e PROGRESS mas deixou AREA PLANTED, AREA HARVESTED, YIELD, PRODUCTION e CONDITION sem inspecao. Resultado: na implementacao do DEBT-01 o agente assumiu padrao de short_desc errado para AREA (esperou "MEASURED IN ACRES", recebeu "ACRES PLANTED"), precisou rodar probe focado em runtime para corrigir. Licao: probe-first significa cobrir todas as categorias que serao consumidas pelo client, nao apenas uma amostra representativa.

### L08 — Ciclo "falha no teste → probe focado → correcao" funciona dentro da mesma sessao
**Data:** 23/05/2026
Quando um filtro sobre dado de API governamental retorna vazio, a hipotese mais provavel e divergencia entre o formato real e o presumido — nao bug de logica do client. Padrao validado nesta sessao: rodar probe targeted contra o endpoint especifico, comparar com o filtro, ajustar, re-rodar suite. O Claude Code executou esse ciclo autonomamente para o `get_acreage` em poucos minutos, sem precisar de nova rodada de validacao humana.

---

*Fim do documento — DECISIONS_LOG.md*

# ROADMAP — Safra Radar
**Versao | 21/05/2026 | Plano por fases**

> Plano de fases do Safra Radar com criterios de aceitacao por fase. Cada fase so avanca apos validacao manual de Eduardo. Fases nao tem deadline rigido — disciplina e mais importante que velocidade.

---

## Fase 0 — Fundacao
**Objetivo:** estabelecer governanca, disciplina e infraestrutura minima.

**Entregaveis:**
- Repositorio GitHub `eduardopfranca/safra-radar` criado
- Pasta `docs/` populada com: README, SPEC_CONSOLIDADA, DECISIONS_LOG, DATA_SOURCES, AGENTS_BOUNDARIES, ROADMAP
- Projeto Supabase novo criado, projeto ID registrado em DECISIONS_LOG
- Conta Render configurada para o backend (mesmo plano que Safra Segura)
- Estrutura de pastas inicial (`api/`, `engines/`, `tools/`, `connections/`, `scripts/`, `tests/`)
- `requirements.txt` minimo (fastapi, uvicorn, requests, pydantic, python-dotenv)
- README do projeto Claude (CLAUDE.md — memoria + instrucoes + descricao)

---

## Fase 1 — Provas de fonte (probes)
**Objetivo:** validar viabilidade real de cada fonte de dado do MVP antes de investir em arquitetura.

**Entregaveis:**
- Para cada fonte, um script `scripts/probe_<fonte>.py` que:
  - Conecta na fonte
  - Retorna o dado bruto cru
  - Imprime o tempo de resposta e o formato
- Atualizacao de DATA_SOURCES.md com status real (`✅ Validado` / `⚠️ Candidato com ressalva` / `❌ Rejeitado`) por fonte, mais nota de probe

**Sem persistencia, sem frontend.** So provar que da pra puxar.

**Criterio de aceitacao:** tabela em DATA_SOURCES.md preenchida com status real. Cada fonte tem nota de probe registrada.

---

## Fase 2 — Backend MVP
**Objetivo:** API REST funcional cobrindo todos os blocos do MVP.

**Entregaveis:**
- `connections/` populado com adapters validados na fase 1
- `engines/price_conversion.py` (USD cents/bushel <> R$/saca)
- `api/main.py` + routers por dominio:
  - `prices.py` — GET /prices/futures, GET /prices/spot
  - `calendar.py` — GET /calendar/events
  - `reports.py` — GET /reports/stocks, GET /reports/latest-analysis
  - `climate.py` — GET /climate/enso
  - `premium.py` — GET /premium/paranagua
- Schemas Pydantic completos
- Schema Supabase com tabelas `data_snapshots`, `events`, `editorial_notes`
- Edge Function `api-proxy` no Supabase (igual ao Safra Segura)
- Deploy no Render

**Criterio de aceitacao:** chamadas curl autenticadas retornam JSON consistente para cada endpoint do MVP. Cada resposta inclui `source`, `fetched_at`, `source_timestamp`. Persistencia em `data_snapshots` validada (JSONB inteiro, sem cherry-pick).

---

## Fase 3 — Frontend MVP
**Objetivo:** tela unica funcional para usuario final.

**Entregaveis:**
- Projeto Lovable conectado ao Supabase (cliente JS) e a Edge Function
- Tela unica com cards por bloco:
  - Precos futuros (CBOT soja, CBOT milho, B3 milho)
  - Cambio
  - Calendario de eventos
  - Estoques USDA
  - ENSO
  - Premio porto Paranagua
- Cada card com: dado principal, contexto pequeno, fonte + timestamp, botao "atualizar", badge de desatualizacao
- Linguagem em PT do produtor (validar contra DECISIONS_LOG D05)
- Mirror em Vercel ativo
- Dominio definitivo (decisao pendente)

**Criterio de aceitacao:** Eduardo abre a tela em primeira pessoa, **fingindo ser um produtor de 1.500 ha em Sorriso**, e consegue em 30 segundos:
- Saber o preco da saca de soja e milho hoje
- Saber se houve alta ou baixa
- Saber qual o proximo evento relevante
- Saber se estamos em El Nino ou La Nina

Se algum desses 4 nao for evidente em 30s, fase nao avancou.

---

## Fase 4 — Analise rapida pos-evento
**Objetivo:** transformar dado bruto de evento USDA em leitura digerida.

**Entregaveis:**
- Heuristica simples no backend: dado estoque USDA vs. consenso → vies (altista/baixista/neutro)
  - Consenso pode ser cadastrado manualmente no Supabase pre-evento
- Editor manual: Eduardo (ou Claude orquestrado) escreve 2–3 linhas em portugues por evento
- Card "Analise rapida" no frontend mostra: vies (cor + icone), texto editorial, fonte, link para PDF original

**Criterio de aceitacao:** pelo menos 1 WASDE coberto com analise (vies + texto). Disclaimer visivel: "Esta nao e recomendacao de venda." (alinhamento com D04).

---

## Fase 5 — Historico e didatica (pos-MVP)
**Objetivo:** dar contexto historico ao dado pontual.

**Entregaveis:**
- Grafico CBOT 12 meses
- Grafico premio porto 12 meses
- Grafico historico ENSO
- Cards educacionais ("O que e WASDE?", "O que e premio porto?", "Como ler o cambio?")
- GLOSSARY.md materializado em tooltips do frontend

**Criterio de aceitacao:** usuario nao especialista consegue navegar de um dado pontual para o contexto historico em 1 clique.

---

## Fase 6 — Integracao com Safra Segura (opcional)
**Objetivo:** disponibilizar endpoints do Safra Radar para o Safra Segura consumir.

**Entregaveis:**
- Integracao como modulo do Safra Segura definida com criterio generico; detalhes operacionais a definir quando a fase for iniciada.

---

## Fora do roadmap (registrado para nao esquecer)

| Item | Razao de adiamento |
|---|---|
| Login / multi-tenant / perfil de usuario | Validar conteudo e adesao antes de investir em auth |
| Monetizacao (assinatura, freemium, patrocinio) | Mesmo motivo |
| App mobile nativo | Web responsivo basta no comeco |
| Recomendacao automatica via LLM | Requer maturidade do produto e aval explicito em DECISIONS_LOG |
| Personalizacao por safra do usuario | Fase 2+, depende de login |
| Push / email / notificacoes | Pos-MVP |
| Basis regional fino (MT, GO, PR) | Pos-MVP, depende de IMEA/IEA/Deral |
| Outras commodities (algodao, cafe, trigo) | Pos-MVP |
| Backtest / simulacao de cenarios | Pos-MVP |
| Recomendacao de venda | **Nunca**, sem aval explicito de Eduardo em DECISIONS_LOG |

---

## Disciplina de avanco entre fases

1. Cada fase termina com **revisao manual de Eduardo** contra o criterio de aceitacao.
2. Antes de iniciar fase seguinte: atualizar DECISIONS_LOG com licoes aprendidas da fase anterior.
3. Nenhuma fase pula etapa. Se uma fonte falhou na fase 1, nao avancar para fase 2 sem fallback registrado.
4. Mudancas de escopo durante uma fase exigem registro em DECISIONS_LOG **antes** de implementar.

---

*Fim do documento — ROADMAP.md*

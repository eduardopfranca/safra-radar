# SPEC_CONSOLIDADA — Safra Radar
**Versao | 21/05/2026 | Especificacao consolidada de produto e arquitetura**

---

## 1. Identidade do produto

**Nome:** Safra Radar
**Empresa:** Madcap
**Tagline interna:** "Bloomberg do produtor medio brasileiro"
**Tagline publica (proposta, sujeita a refino):** "Mercado de soja e milho explicado"

### 1.1 Posicionamento

Portal de inteligencia de mercado de soja e milho voltado ao produtor brasileiro medio (500–3.000 ha). Entrega informacao de mesa de hedge premium, traduzida em linguagem do campo, com curadoria editorial e visual claro.

### 1.2 Modelo de negocio

Modulo do Safra Segura. Funciona como **isca para originacao Madcap**: o produtor consome informacao gratuitamente (ou em modelo a definir), entende o potencial de operacoes de hedge/comercializacao, e procura a mesa Madcap para executar. Remuneracao alvo: **0,3–0,5% do volume financeiro originado**.

Monetizacao direta (assinatura, freemium, patrocinio) **nao esta no escopo do MVP**. Decisao deliberada: validar conteudo e adesao antes de monetizar.

### 1.3 Promessa ao usuario

1. Informacao curada e confiavel, com fonte citada e timestamp em cada bloco.
2. Linguagem traduzida: "preco da saca", "trava", "premio porto", "alta/baixa". Termos tecnicos so com glossario inline.
3. Visual claro: cards autocontidos, leitura de status em 30 segundos.
4. Contexto historico para apoio a decisao (medias, comparativos, faixas).
5. **Nunca recomenda venda.** Decisao e do produtor.

### 1.4 Publico-alvo

- **Tamanho:** medio (500–3.000 ha) — entende preco, mexe com cooperativa, mas nao acompanha CBOT diariamente.
- **Cultura:** soja + milho (safra/safrinha).
- **Geografia:** Brasil inteiro, generico no MVP (sem basis regional fino).
- **Dor #1:** "Nao sei quando vender" (timing de comercializacao).
- **Dor #2:** "Nao entendo por que o preco subiu/caiu" (interpretacao de movimento).

---

## 2. Escopo do MVP

### 2.1 Conteudo obrigatorio do MVP

Cada item abaixo e um **bloco visual independente** na tela principal, com botao "atualizar" proprio e badge de desatualizacao (timestamp da ultima leitura + alerta visual quando passa do threshold de cada bloco).

| Bloco | Conteudo | Fonte primaria | Fallback |
|---|---|---|---|
| **Precos futuros** | CBOT soja + milho, B3 milho — preco corrente e variacao do dia, convertido em R$/saca | yfinance | B3 Up2Data (milho) |
| **Cambio** | USD/BRL spot (PTAX) | BCB SGS | yfinance |
| **Calendario de eventos** | Proximos eventos relevantes (WASDE, Crop Progress, Export Sales, ENSO update) com data e impacto esperado | USDA + datas fixas hardcoded | — |
| **Analise rapida pos-evento** | Resumo do ultimo evento USDA com vies (alta/baixa/neutro) traduzido em PT | Editorial (Eduardo + Claude) ou heuristica simples | — |
| **Estoques USDA** | Estoque final mais recente de soja e milho (EUA e mundo) | NASS Quick Stats API + WASDE | — |
| **ENSO (El Nino / La Nina)** | Probabilidade dos proximos 3 trimestres + status atual | NOAA CPC | IRI Columbia |
| **Premio porto** | Premio Paranagua soja (CBOT cents/bu) — corrente e variacao | Scraping Noticias Agricolas | CEPEA/ESALQ |

### 2.2 Comportamento de atualizacao (MVP)

Pull-based. **Sem cronjob** no MVP. Cada bloco tem:
- Botao "atualizar" (refetch sob demanda)
- Timestamp da ultima atualizacao
- Badge visual de desatualizacao quando passa do threshold (threshold proprio por bloco — ex: precos 15min, calendario 24h, ENSO 7d)

Quando o usuario abre a tela, os blocos exibem o ultimo dado em cache. So refetcham se o usuario clicar.

### 2.3 Comportamento visual

- **Tela unica** no MVP (sem navegacao multi-rota).
- Cards autocontidos, sem dependencia visual entre cards.
- Cada card tem: titulo, dado principal grande, contexto pequeno (variacao, comparativo), fonte + timestamp, botao atualizar.
- Linguagem em portugues, tom direto, sem jargao financeiro sem glossario.

---

## 3. Fora do escopo do MVP

Lista explicita do que **nao** sera entregue no MVP. Decisoes deliberadas, com justificativa breve.

| Item | Por que esta fora |
|---|---|
| **Recomendacao de venda** | Decisao filosofica e juridica. Nunca, mesmo em fases futuras, sem aval explicito de Eduardo. |
| **Personalizacao por safra do usuario** ("tenho 2.000 sacas para vender ate marco") | Fase 2+. Exige cadastro e perfil. |
| **Login / multi-tenant** | Fase 2+. MVP e portal aberto, anonimo. |
| **Cobranca / assinatura** | Fase 2+. Validar conteudo e adesao antes. |
| **Push / email / notificacoes** | Pos-MVP. |
| **Basis regional fino** (basis MT, GO, PR separados) | Pos-MVP. MVP usa premio porto Paranagua como proxy nacional. |
| **Recomendacao automatica via LLM sobre dado bruto** | Pos-MVP. MVP usa heuristica simples + editorial humano. |
| **App mobile nativo** | Pos-MVP. MVP e web responsivo. |
| **Integracao com Safra Segura** | Pos-MVP (fase 6). MVP e standalone. |
| **Cobertura de outras commodities** (algodao, cafe, trigo) | Pos-MVP. MVP e soja + milho. |
| **Backtest / simulacao de cenarios** | Pos-MVP. |

---

## 4. Arquitetura

### 4.1 Stack

| Camada | Tecnologia |
|---|---|
| **Backend/API** | Python 3.11+ + FastAPI |
| **Hospedagem backend** | Render |
| **Banco de dados** | Supabase (PostgreSQL) — projeto **novo, dedicado** |
| **Proxy/Auth** | Supabase Edge Function (`api-proxy`) |
| **Frontend** | React/TypeScript via Lovable |
| **Mirror frontend** | Vercel |
| **Repositorio** | GitHub `eduardopfranca/safra-radar` (conta pessoal) |
| **Domain/DNS** | A definir |

### 4.2 Hierarquia de dependencia (inviolavel)

```
scripts/  →  connections/  →  tools/  →  engines/  →  utils.py / helpers.py
                                                            ↑
                                            api/ (importa de qualquer nivel abaixo)
```

Nenhuma camada importa de camadas acima. Engines sao calculo puro — sem I/O, sem banco, sem efeitos colaterais. Atomicos sempre em `utils.py` ou `helpers.py`.

### 4.3 Estrutura de pastas (proposta inicial)

```
safra-radar/
├── README.md
├── CLAUDE.md
├── .gitignore
├── requirements.txt
├── docs/
│   ├── README.md
│   ├── SPEC_CONSOLIDADA.md
│   ├── DECISIONS_LOG.md
│   ├── DATA_SOURCES.md
│   ├── AGENTS_BOUNDARIES.md
│   └── ROADMAP.md
├── api/
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── routers/
│   │   ├── prices.py          # CBOT, B3, USD/BRL
│   │   ├── calendar.py        # eventos USDA + ENSO update
│   │   ├── reports.py         # WASDE, NASS Quick Stats, analise pos-evento
│   │   ├── climate.py         # ENSO, clima regional opcional
│   │   ├── premium.py         # premio porto
│   │   └── news.py            # noticias curadas (opcional MVP)
│   └── schemas/
├── engines/                   # calculo puro
│   └── (a definir na Fase 2)
├── tools/                     # orquestracao
├── connections/               # adapters externos (1 arquivo por fonte)
│   ├── yfinance_fetcher.py
│   ├── cepea_fetcher.py
│   ├── usda_nass_fetcher.py
│   ├── noaa_enso_fetcher.py
│   ├── noticias_agricolas_fetcher.py
│   └── (etc.)
├── scripts/                   # pontas: probes, debug, backfill
│   ├── probe_yfinance.py
│   ├── probe_cepea.py
│   └── (etc.)
├── utils.py
├── helpers.py
├── tests/
└── requirements.txt
```

### 4.4 Padrao de Edge Function

Lovable nunca chama a API Python diretamente. Toda chamada passa pela Edge Function `api-proxy` no Supabase, que adiciona `X-API-Key` via secret. Razao: API key do Render nao pode ser exposta no frontend.

### 4.5 Schema Supabase inicial (proposta)

Schema minimo para MVP. Detalhamento real em DECISIONS_LOG quando criado.

| Tabela | Conteudo |
|---|---|
| `data_snapshots` | Cache de leituras por fonte: `(source, key, payload JSONB, fetched_at, source_timestamp)`. JSONB inteiro, sem cherry-pick. |
| `events` | Calendario de eventos com `event_type`, `scheduled_at`, `published_at`, `impact_summary`, `bias` (bullish/bearish/neutral), `editorial_note` |
| `editorial_notes` | Notas pos-evento escritas por humano: `(event_id, author, body_md, published_at)` |

RLS: leitura publica no MVP (sem login). Escrita restrita por API key.

---

## 5. Regras inviolaveis de codigo

1. **Todo codigo em ingles.** Variaveis, docstrings, prints, logs, nomes de metodos, comentarios.
2. **Engines sao calculo puro.** Sem I/O, sem banco, sem chamadas externas, sem efeitos colaterais.
3. **Atomicos sempre em utils/helpers.** Engines orquestram, nunca reimplementam calculo proprio.
4. **Hierarquia de import inviolavel:** `scripts → connections → tools → engines → utils/helpers`.
5. **Nunca calcular no frontend.** Toda conta e na API Python.
6. **Persistir objetos JSONB inteiros.** Nunca cherry-pick ao salvar resposta de API em coluna JSONB.
7. **Conversoes de unidade so nas fronteiras** entre camadas. Documentar cada ponto canonico.
8. **Citar fonte e timestamp** em todo endpoint de dado externo.
9. **Em caso de duvida:** parar e perguntar.

---

## 6. Glossario rapido

| Termo PT (publico) | Termo tecnico | Significado curto |
|---|---|---|
| Premio porto | Basis FOB | Diferenca entre preco no porto e CBOT, em USD cents/bu |
| Trava | Hedge / venda futura | Operacao que fixa preco de venda antecipado |
| Saca | Bag | 60 kg de soja ou milho |
| Bushel | Bushel | Unidade CBOT — soja: 27,2155 kg; milho: 25,4012 kg |
| WASDE | World Agricultural Supply and Demand Estimates | Relatorio mensal USDA de oferta/demanda global |
| ENSO | El Nino Southern Oscillation | Fenomeno climatico — El Nino e La Nina sao suas duas fases |
| Estoque final | Ending stocks | Estoque previsto ao fim da safra |
| Alta / Baixa | Bullish / Bearish | Vies de preco |

Glossario completo sera mantido em `GLOSSARY.md` quando o frontend precisar.

---

## 7. Disciplina de processo

1. **Debate-first, code-after:** arquitetura sempre debatida antes de implementacao.
2. **Uma etapa por vez:** uma decisao, um arquivo, um prompt. Aguardar confirmacao antes de avancar.
3. **Multi-agente com fronteiras estritas:** ver `AGENTS_BOUNDARIES.md`.
4. **Eduardo administra git manualmente** — `git push origin main`. Claude Code nunca da push sem instrucao explicita.
5. **Nunca trabalhar em arquivo sem o conteudo completo colado no chat.**
6. **Validar antes de avancar** — manual review apos cada fase.

---

*Fim do documento — SPEC_CONSOLIDADA.md*

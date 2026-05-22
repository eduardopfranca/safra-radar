# AGENTS_BOUNDARIES — Safra Radar
**Versao | 21/05/2026 | Fronteiras de execucao**

> Referencia de fronteiras de responsabilidade entre os agentes de execucao do projeto.
> Consultar antes de redigir qualquer prompt de execucao ou planejar tarefa multi-camada.
> Regra derivada: ver P04 em DECISIONS_LOG.md.

---

## Agentes e suas camadas

| Agente | Atua em | Nunca toca |
|---|---|---|
| **Claude (arquiteto, no chat)** | Planejamento, debate arquitetural, revisao de codigo, redacao de prompts para os outros agentes. Atualiza documentacao `.md` do projeto quando solicitado. | Execucao direta de codigo ou comandos. Nunca edita arquivos de codigo diretamente — sempre via prompt para Claude Code ou Lovable. |
| **Claude Code** | Codigo Python da API, engines, tools, utils, helpers, connections, scripts. Testes locais via uvicorn. `requirements.txt`. Documentacao `.md` do repositorio Python. | Supabase. Lovable. Render. Qualquer coisa fora do repositorio Python. |
| **Lovable** | Frontend React, chamadas a Edge Function `api-proxy`, leitura via cliente JS Supabase de tabelas publicas (cache de snapshots, calendario, editorial), UI, estado, formularios, exibicao. | API Python (chamada direta). |
| **Supabase Dashboard** | SQL migrations, Edge Functions, secrets, RLS policies, triggers, constraints, criacao/edicao de tabelas, funcoes PL/pgSQL. | — |
| **Render Dashboard** | Env vars do backend, deploy settings, upgrade de plano, logs de producao. | — |
| **Eduardo (humano)** | `git push origin master:main`, decisoes de negocio, configuracao manual de Supabase/Render/Vercel/Lovable, validacao por fase. | — |

---

## Teste obrigatorio antes de qualquer prompt de execucao

> **"Este prompt toca apenas uma camada?"**

Se a resposta for **nao**, Claude deve parar, explicitar as camadas envolvidas no chat com Eduardo, e decompor o trabalho em prompts separados — um por agente. Nunca empilhar responsabilidades cruzadas num unico prompt.

---

## Red flags que indicam violacao da fronteira

**Em prompt destinado a Claude Code:**
- "rode esta migration" / "crie este SQL" → migrations vao para Supabase Dashboard manual
- "instancie cliente Supabase" / "leia a tabela X" → API Python nao le o banco diretamente. Frontend ou Edge Function fazem.
- "adicione `SUPABASE_URL` como env var" → env vars sao configuradas manualmente no Render Dashboard
- "atualize o Lovable para..." → Lovable e camada separada
- Tabelas do banco mencionadas como dependencia de runtime da API Python → sinal de que a arquitetura esta errada

**Em prompt destinado ao Lovable:**
- "implemente este calculo" / "calcule X no frontend" → calculo e sempre na API Python
- "crie esta Edge Function" → Edge Functions vao para Supabase Dashboard manual
- "altere o schema da tabela X" → schema e migration SQL manual
- "chame a API do Render direto" → toda chamada e via Edge Function `api-proxy`

**Em prompt destinado a qualquer agente:**
- Mencionar mais de uma das camadas da tabela acima como alvo de mudanca → decompor antes de enviar
- Pedir para Claude Code dar push no GitHub → push e responsabilidade de Eduardo

---

## Padroes globais de integracao

Regras meta que se aplicam a qualquer integracao presente ou futura entre camadas.

### Persistir objetos JSONB inteiros
Ao salvar resposta de API em campo JSONB do Supabase, persistir o objeto inteiro via spread (`{...result}`), nao fazer cherry-pick de campos. Cherry-pick so e aceitavel quando o campo descartado tem custo real de storage ou performance, o que raramente e o caso.

### Derivar campos deterministicos na API, nao no frontend
Campos que podem ser derivados de outros com regra deterministica (ex: `currency` a partir de `commodity + exchange`) devem ter essa derivacao no router da API Python, nao no Lovable. Frontend passa opcional, API preenche quando ausente.

### Unidades canonicas por camada
Cada camada do sistema tem sua unidade canonica para cada campo monetario/quantitativo. Conversoes acontecem apenas nas fronteiras entre camadas — nunca no meio de uma funcao, query ou componente. Antes de tocar em qualquer codigo envolvendo precos, cambio ou conversao, consultar `UNITS_REFERENCE.md` (quando criado).

### Nunca duplicar logica de negocio entre camadas
Se uma regra existe na API Python, o Lovable nao pode reimplementar — deve chamar a API.

### Citar fonte e timestamp em todo dado externo
Todo endpoint que retorna dado externo (preco, evento, indicador) inclui no payload: `source`, `source_url` (opcional), `fetched_at` (ISO 8601), `source_timestamp` quando disponivel. Lovable exibe ao usuario.

---

## Padrao de integracao Render <> Supabase <> Lovable

```
Usuario abre Lovable
   |
Lovable le ultimo snapshot do Supabase (cliente JS)
   |
Se snapshot esta dentro do threshold → exibe direto + badge "atualizado ha Xmin"
Se usuario clica "atualizar" → Lovable chama Edge Function api-proxy
   |
Edge Function adiciona X-API-Key e chama Python API no Render
   |
Python API consulta fonte externa (yfinance, CEPEA, etc.)
   |
Python API retorna JSON para Edge Function
   |
Edge Function escreve em data_snapshots (UPSERT) e retorna para Lovable
   |
Lovable atualiza UI
```

---

*Fim do documento — AGENTS_BOUNDARIES.md*

# README — Safra Radar
**Versao | 21/05/2026 | Produto comercial Madcap**

## O que e este projeto

Portal de inteligencia de mercado de soja e milho para produtor brasileiro medio (500–3.000 ha). Produto da Madcap. Funciona como isca de originacao: o produtor consome informacao curada de qualidade e procura a mesa Madcap quando ve potencial de operacao (remuneracao alvo 0,3–0,5% do volume financeiro).

Promessa de produto: "Bloomberg do produtor medio" — informacao de mesa premium, traduzida e acessivel. Calendario de eventos, precos em R$/saca, cambio, premio porto, ENSO, analise rapida pos-evento USDA. Nunca recomenda venda. Entrega dado + contexto + visual claro; decisao e do produtor.

**Stack:**
- **Backend/API:** Python + FastAPI, deploy no Render
- **Frontend:** Lovable (React/TypeScript)
- **Banco de dados:** Supabase (PostgreSQL)
- **Repositorio:** GitHub `eduardopfranca/safra-radar`

---

## Instrucao para o Claude

1. `SPEC_CONSOLIDADA.md` — fonte de verdade de regras de produto e arquitetura
2. `DECISIONS_LOG.md` — decisoes arquiteturais, padroes de trabalho e licoes aprendidas
3. `DATA_SOURCES.md` — catalogo de fontes externas, viabilidade, risco e fallback
4. `AGENTS_BOUNDARIES.md` — fronteiras entre agentes executores
5. `ROADMAP.md` — fases do produto e criterios de aceitacao

**Se qualquer ponto estiver ambiguo para a tarefa em maos, PARE e pergunte ao Eduardo. Nunca assuma comportamento nao descrito.**

---

## Documentacao do projeto

| Arquivo | Conteudo |
|---|---|
| `SPEC_CONSOLIDADA.md` | Fonte de verdade de visao, MVP, escopo, nao-escopo, regras inviolaveis |
| `DECISIONS_LOG.md` | Decisoes arquiteturais datadas, padroes de trabalho, licoes aprendidas |
| `DATA_SOURCES.md` | Catalogo completo de fontes externas: URL, metodo, frequencia, qualidade, risco, fallback |
| `AGENTS_BOUNDARIES.md` | Quem faz o que: Claude, Claude Code, Lovable, Supabase Dashboard, Render Dashboard, Eduardo |
| `ROADMAP.md` | Fases 0–6 com criterios de aceitacao por fase |

Arquivos que **nao existem ainda** e podem ser criados conforme o projeto evoluir:

- `CODE_REFERENCE.md` — modulos, classes, metodos do backend Python (cria quando houver codigo Python ativo)
- `FRONTEND_REFERENCE.md` — telas, state machines, pontos de conversao (cria quando houver telas no Lovable)
- `INFRA_REFERENCE.md` — deploy, env vars, integracao (cria quando subir Render/Vercel)
- `UNITS_REFERENCE.md` — unidades canonicas por camada (cria quando houver conversao USD↔BRL em producao)
- `GLOSSARY.md` — termos de mercado em PT para uso consistente

---

## Regras de trabalho

1. **Fonte de verdade:** `SPEC_CONSOLIDADA.md`. Em caso de conflito entre qualquer outro arquivo e a spec, a spec prevalece.
2. **Todo codigo em ingles** — variaveis, docstrings, prints, logs, nomes de metodos.
3. **Engines sao calculo puro** — sem I/O, sem banco, sem efeitos colaterais.
4. **Usar utils/helpers existentes** — nunca reimplementar logica que ja existe.
5. **Hierarquia de dependencia:** `scripts → connections → tools → engines → utils/helpers`. Nenhuma camada importa de camadas acima. A camada `api/` e a unica que pode importar de qualquer camada abaixo.
6. **Calculos atomicos SEMPRE em utils/helpers** — engines sao orquestradores, nao implementam calculo proprio.
7. **Nunca calcular no frontend** — toda conta e na API Python.
8. **Persistir objetos JSONB inteiros** — nunca cherry-pick de campos quando armazenar resposta de API em coluna JSONB.
9. **Conversoes de unidade so nas fronteiras** entre camadas.
10. **Em caso de duvida:** nao assuma. Pergunte ao Eduardo.

---

## Promessa do produto (resumo)

- Informacao curada de qualidade, em linguagem do produtor.
- **Nunca recomenda venda.** Entrega dado + contexto historico + visual claro.
- Fontes sempre citadas com timestamp.
- Atualizacao pull-based no MVP: botao "atualizar" por bloco + badge de desatualizacao.

---

*Fim do documento — docs/OVERVIEW.md*

# DEBT.md — Safra Radar

**Versao | 22/05/2026 | Append-only**

> Registro de divida tecnica conhecida e scope deliberadamente adiado.
> Cada entrada inclui contexto suficiente para retomar o trabalho sem depender de memoria de sessao.

---

## Pendencias abertas

### DEBT-01 — USDA NASS: categorias nao implementadas

**Registrado:** 22/05/2026
**Arquivo:** `connections/usda_nass_client.py`

As seguintes categorias foram descobertas no probe de 22/05/2026 e validadas como existentes na API, mas nao foram implementadas como metodos publicos:

- **Crop Condition** (semanal): percentual de cultura em cada nivel (VERY POOR / POOR / FAIR / GOOD / EXCELLENT).
- **Acreage** (anual): area plantada e colhida final de safra, categoria separada de PROGRESS.
- **Yield** (anual): produtividade por acre, categoria separada de PRODUCTION.
- **Production** (anual): producao total em bushels.
- **Sibling de comparacao** para Condition e Progress: dado do ano anterior e media de 5 anos disponivel via parametros adicionais.

Implementar na proxima sessao dedicada ao NASS.

---

### DEBT-02 — USDA ESR: client nao criado

**RESOLVIDO em 23/05/2026** — client implementado em connections/usda_esr_client.py com get_weekly_exports, get_weekly_exports_series, get_latest_week, list_commodities, list_countries. 4 commodities, China nomeada, demais via allCountries. Testado contra dados reais 2026-05-14.

**Registrado:** 22/05/2026
**Arquivo:** a criar em `connections/usda_esr_client.py`

Probes validaram os endpoints em `scripts/probe_usda_esr.py`. Escopo confirmado:

- Commodities: Corn (401), Soybeans (801), Soybean Meal (901), Soybean Oil (902).
- China como country code 5700 (nomeado).
- Demais destinos via endpoint `allCountries`.
- Autenticacao via header `X-Api-Key` (diferente do PSD que usa query param).

Herdar de `BaseUSDAClient` com `AUTH_METHOD = "header"`. Criar na proxima sessao.

---

### DEBT-03 — USDA PSD: attributeId 195 (Stocks-to-Use) opcional

**Registrado:** 22/05/2026
**Arquivo:** `connections/usda_fas_client.py`

O atributo `attributeId=195` (Stocks-to-Use) foi adicionado ao mapeamento `ATTRIBUTES` do `USDAFasClient`, mas nao e retornado pela API para todas as combinacoes commodity/country. O client ja trata isso graciosamente (silently skip), mas consumidores downstream devem tratar a chave "Stocks-to-Use" como opcional no dict retornado — nunca assumir presenca.

---

### DEBT-04 — USDA PSD: EU-27 e World aggregate nao implementados

**Registrado:** 22/05/2026
**Arquivo:** `connections/usda_fas_client.py`, `COUNTRIES` mapping

O PSD usa codigos como E2/E3/E4 para agrupamentos distintos da Uniao Europeia, mas nao tem um agregado global "World" com codigo unico. Se necessario downstream, construir somando os paises principais. Nao adicionar ao `COUNTRIES` mapping antes de validar qual codigo EU-27 retorna os dados corretos via probe.

---

### DEBT-05 — ESR Weekly Exports: candidato a cron

**Registrado:** 22/05/2026
**Contexto:** arquitetura atual e pull-based (D03)

O relatorio ESR de exportacoes e publicado toda quinta-feira pelo USDA. Quando o volume de usuarios justificar, migrar de pull-only para fetch agendado + push notification. Candidato natural para primeiro cronjob do produto. Registrar revisao de D03 no DECISIONS_LOG quando implementar.

---

*Fim do documento — DEBT.md*

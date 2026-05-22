# DATA_SOURCES — Safra Radar
**Versao | 21/05/2026 | Catalogo de fontes externas**

> Catalogo de todas as fontes de dado consideradas para o produto. Status pode ser:
> - ✅ **Validado** — provado em probe, em uso no MVP
> - ⚠️ **Candidato** — viavel a principio, falta validar
> - ❌ **Rejeitado** — testado e descartado, com motivo registrado

---

## 1. Precos de futuros

### 1.1 yfinance (CBOT soja, CBOT milho, USD/BRL) — ⚠️

### 1.2 B3 Up2Data (milho B3) — ⚠️

### 1.3 CME Group (CBOT direto) — ⚠️

---

## 2. Cambio

### 2.1 BCB SGS (Sistema Gerenciador de Series Temporais) — ⚠️

### 2.2 yfinance USDBRL=X — ⚠️

### 2.3 AwesomeAPI — ⚠️

---

## 3. Indicadores spot Brasil (preco saca)

### 3.1 CEPEA/ESALQ — ⚠️

### 3.2 IMEA (Instituto Mato-grossense de Economia Agropecuaria) — ⚠️

### 3.3 IEA SP, Deral PR, outros estaduais — ⚠️

---

## 4. Premio porto

### 4.1 Noticias Agricolas (scraping) — ⚠️

### 4.2 CMA (Consultoria/Methods/Assessoria) — ❌ para MVP

### 4.3 StoneX — ❌ para Safra Radar
- **Motivo:** acesso interno de Eduardo (Safra Segura). Nao pode ser exposto no Safra Radar publico — quebra contrato de uso e expoe dado de terceiro pagante.

---

## 5. USDA — relatorios oficiais

### 5.1 USDA NASS Quick Stats — ⚠️

### 5.2 USDA WASDE — ⚠️

### 5.3 USDA FAS Export Sales — ⚠️

### 5.4 USDA FAS PSD Online — ⚠️

---

## 6. Clima e ENSO

### 6.1 NOAA CPC ENSO — ⚠️

### 6.2 IRI Columbia ENSO — ⚠️

### 6.3 Open-Meteo — ⚠️

### 6.4 NOAA NWS Crop Belt (EUA) — ⚠️

---

## 7. Posicionamento de fundos (sentimento)

### 7.1 CFTC Commitments of Traders — ⚠️

---

## 8. Noticias

### 8.1 Noticias Agricolas RSS — ⚠️

### 8.2 Reuters Ag — ❌ para MVP

### 8.3 Bloomberg Ag — ❌ para MVP

---

## 9. Calendario economico

### 9.1 Investing.com — ⚠️

### 9.2 Trading Economics — ⚠️

### 9.3 FRED (Fed) — ⚠️

---

## 10. Resumo — fontes do MVP

> Tabela a ser preenchida ao final da Fase 1 (probes). Status inicial: todos os candidatos do MVP em ⚠️.

| Bloco MVP | Fonte primaria | Fallback | Status |
|---|---|---|---|
| Precos futuros | yfinance | B3 Up2Data | ⚠️ |
| Cambio | BCB SGS | yfinance | ⚠️ |
| Calendario de eventos | USDA + datas fixas | — | ⚠️ |
| Analise rapida pos-evento | Editorial / heuristica | — | ⚠️ |
| Estoques USDA | NASS Quick Stats + WASDE | — | ⚠️ |
| ENSO | NOAA CPC | IRI Columbia | ⚠️ |
| Premio porto | Noticias Agricolas | CEPEA/ESALQ | ⚠️ |

---

*Fim do documento — DATA_SOURCES.md*

"""
Probe: NOAA CPC ENSO Data Products
Cobre quatro endpoints validados:
  1. Oceanic Nino Index (ONI) — serie historica numerica
  2. SST Regional Indices — Nino 1+2 / 3 / 4 / 3.4 mensais
  3. ENSO Diagnostic Discussion — texto oficial mensal
  4. RONI Probabilities — tabela de probabilidades por 9 estacoes moveis
Sem dependencias alem de requests.
"""

import re
import time
import requests

TIMEOUT = 25
UA = {"User-Agent": "SafraRadar-probe/1.0 (research; not scraping)"}

SEP = "=" * 72


def fetch(label, url, note=""):
    print(f"\n{SEP}")
    print(f"  {label}")
    print(f"  URL   : {url}")
    if note:
        print(f"  Note  : {note}")
    print(SEP)
    t0 = time.perf_counter()
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=UA)
        elapsed = time.perf_counter() - t0
        ct = r.headers.get("Content-Type", "?")
        enc = r.encoding or "?"
        print(f"  Status       : {r.status_code}  ({elapsed:.2f}s)")
        print(f"  Content-Type : {ct}")
        print(f"  Encoding     : {enc}")
        print(f"  Size         : {len(r.content):,} bytes")
        return r
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


# ---------------------------------------------------------------------------
# Analysers
# ---------------------------------------------------------------------------

def analyse_oni(r):
    """ONI — space-separated ASCII table (year x month)."""
    lines = [l for l in r.text.strip().splitlines() if l.strip()]
    print(f"\n  Lines (total): {len(lines)}")
    print(f"  Header       : {lines[0]}")
    data = [l for l in lines[1:] if not l.startswith("YR")]
    print(f"  Data rows    : {len(data)}")

    first = data[0].split() if data else []
    last  = data[-1].split() if data else []
    if first and last:
        print(f"  Coverage     : {first[0]} — {last[0]}")

    print(f"\n  --- Last 6 rows ---")
    for row in data[-6:]:
        print(f"  {row}")

    # Current ENSO phase: last non-missing monthly value
    if last:
        vals = last[1:]
        non_missing = [(i + 1, v) for i, v in enumerate(vals) if v not in ("-99.9", "-999")]
        if non_missing:
            idx, val = non_missing[-1]
            months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
            phase = "El Nino" if float(val) >= 0.5 else ("La Nina" if float(val) <= -0.5 else "Neutral")
            print(f"\n  Latest value : {months[idx-1]} {last[0]}  ONI={val}  => {phase}")


def analyse_sst_indices(r):
    """SST Regional Indices — monthly Nino 1+2 / 3 / 4 / 3.4 SST and anomaly."""
    lines = [l for l in r.text.strip().splitlines() if l.strip()]
    print(f"\n  Lines (total): {len(lines)}")
    print(f"  Header       : {lines[0][:120]}")

    data = [l for l in lines[1:] if not l.strip().startswith("YR") and not l.strip().startswith("YEAR")]
    print(f"  Data rows    : {len(data)}")
    if data:
        first_cols = data[0].split()
        last_cols  = data[-1].split()
        if first_cols and last_cols:
            print(f"  Coverage     : {first_cols[0]}/{first_cols[1]}  —  {last_cols[0]}/{last_cols[1]}")

    print(f"\n  --- Last 3 rows ---")
    for row in data[-3:]:
        print(f"  {row[:120]}")


def analyse_discussion(r, max_chars=5000):
    """Full text of the ENSO diagnostic discussion."""
    text = r.text.strip()
    print(f"\n  Text length: {len(text):,} chars")

    # Identify ENSO Alert System Status line
    for line in text.splitlines():
        stripped = line.strip()
        if "enso alert system status" in stripped.lower():
            print(f"\n  Alert Status : {stripped}")
            break

    print(f"\n  --- FULL DISCUSSION (up to {max_chars} chars) ---")
    print(text[:max_chars])
    if len(text) > max_chars:
        print(f"\n  ... [{len(text) - max_chars} additional chars omitted] ...")
    print(f"  --- END DISCUSSION ---")


def analyse_roni_probabilities(r):
    """
    RONI Probabilities page — discover format and extract table data.
    Three possible cases:
      A) Static HTML with a parseable <table> — extract season rows
      B) JS-rendered page — HTML is a shell; data comes from adjacent endpoint
      C) Image-only — inviable without OCR
    """
    text = r.text
    lower = text.lower()
    print(f"\n  HTML size: {len(text):,} chars")

    # --- Classify content type ---
    has_table  = "<table" in lower
    has_canvas = "<canvas" in lower
    has_img    = bool(re.search(r'<img\b[^>]+\.(png|gif|jpg|jpeg)', lower))
    script_tags = len(re.findall(r'<script\b', lower))
    print(f"\n  Has <table>  : {has_table}")
    print(f"  Has <canvas> : {has_canvas}")
    print(f"  Has <img>    : {has_img}")
    print(f"  <script> tags: {script_tags}")

    # --- Season codes (9-season horizon marker) ---
    season_re = re.compile(r'\b(JFM|FMA|MAM|AMJ|MJJ|JJA|JAS|ASO|SON|OND|NDJ|DJF)\b')
    seasons_found = season_re.findall(text)
    unique_seq = list(dict.fromkeys(seasons_found))  # preserve insertion order, deduplicate
    print(f"\n  3-month season codes: {len(seasons_found)} occurrences, unique sequence: {unique_seq}")

    # --- Percentage occurrences ---
    pct_count = lower.count("%")
    print(f"  '%' occurrences: {pct_count}")
    pct_positions = [i for i in range(len(lower)) if lower[i] == "%"]
    for i, pos in enumerate(pct_positions[:6]):
        snippet = text[max(0, pos - 90):pos + 60].replace("\n", " ").strip()
        print(f"  pct[{i}]: ...{snippet}...")

    # --- Key ENSO probability keywords ---
    for kw in ["el nino", "la nina", "neutral", "season", "probability", "amj"]:
        idx = lower.find(kw)
        if idx >= 0:
            snippet = text[max(0, idx - 30):idx + 150].replace("\n", " ").strip()
            print(f"\n  Keyword '{kw}' at {idx}: ...{snippet}...")

    # --- Extract <table> rows if present ---
    if has_table:
        print(f"\n  --- TABLE CONTENT (regex extraction) ---")
        # Strip tags inside cells for readability
        cell_re = re.compile(r'<t[dh][^>]*>(.*?)</t[dh]>', re.IGNORECASE | re.DOTALL)
        row_re  = re.compile(r'<tr[^>]*>(.*?)</tr>', re.IGNORECASE | re.DOTALL)
        tag_re  = re.compile(r'<[^>]+>')
        rows = row_re.findall(text)
        for row in rows[:20]:
            cells = cell_re.findall(row)
            cleaned = [tag_re.sub("", c).strip() for c in cells]
            if any(cleaned):
                print(f"  ROW: {cleaned}")
        if len(rows) > 20:
            print(f"  ... [{len(rows) - 20} more <tr> rows] ...")
    else:
        print(f"\n  No <table> tag found — checking for JS data embedding")
        # Look for inline JSON blobs that might carry table data
        json_candidates = re.findall(r'(?:var|const|let)\s+\w+\s*=\s*(\[[\s\S]{20,500}\])', text)
        if json_candidates:
            print(f"  JS array candidates: {len(json_candidates)}")
            for c in json_candidates[:3]:
                print(f"    {c[:200]}")
        else:
            print(f"  No inline JS array found")

    # --- Adjacent / raw data endpoint discovery ---
    print(f"\n  --- HREFS that look like data endpoints ---")
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', text, re.IGNORECASE)
    print(f"  Total hrefs: {len(hrefs)}")
    data_kw = (".txt", ".csv", ".json", ".xml", ".tsv", "data", "table",
               "prob", "enso", "nino", "roni", "outlook")
    data_hrefs = [h for h in hrefs if any(k in h.lower() for k in data_kw)]
    print(f"  Data-looking hrefs: {len(data_hrefs)}")
    for h in data_hrefs[:20]:
        print(f"    {h}")

    # --- src attributes (images, scripts that might load data) ---
    srcs = re.findall(r'src=["\']([^"\']+)["\']', text, re.IGNORECASE)
    data_srcs = [s for s in srcs if any(k in s.lower() for k in data_kw)]
    if data_srcs:
        print(f"\n  Data-looking src attributes: {len(data_srcs)}")
        for s in data_srcs[:10]:
            print(f"    {s}")

    # --- Raw HTML excerpt around first season code or first % ---
    print(f"\n  --- RAW HTML first 3000 chars ---")
    print(text[:3000])
    print(f"  --- END EXCERPT ---")

    # --- Verdict ---
    print(f"\n  === VIABILIDADE ENDPOINT 4 ===")
    if has_table and seasons_found and pct_count >= 9:
        print(f"  => VIAVEL: tabela HTML estatica com {len(unique_seq)} estacoes e {pct_count} valores %")
        print(f"     Parsing via regex <table>/<tr>/<td> funciona sem bs4.")
    elif has_table and seasons_found:
        print(f"  => PARCIAL: tabela HTML presente, {len(unique_seq)} estacoes, mas poucos % ({pct_count})")
        print(f"     Verificar se valores estao em texto ou em imagem dentro das celulas.")
    elif script_tags > 3 and not seasons_found:
        print(f"  => INVIAVEL SEM HEADLESS: conteudo parece renderizado via JS ({script_tags} <script> tags)")
        print(f"     Nenhum season code encontrado no HTML estatico — dado nao esta no source.")
    elif has_img and not seasons_found:
        print(f"  => INVIAVEL: dados provavelmente em imagem — requer OCR.")
    else:
        print(f"  => INCONCLUSIVO: revisar raw HTML acima para determinar estrutura.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(SEP)
    print("  PROBE: NOAA CPC ENSO — 4 endpoints validados")
    print("  1. ONI historico  2. SST Regional  3. Discussion  4. RONI Probabilities")
    print(SEP)

    # --- PRODUCT 1: ONI historical ---
    r = fetch(
        "PRODUCT 1 — Oceanic Nino Index (ONI) — historical series",
        "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        "Rolling 3-month SST anomaly for Nino 3.4 region. El Nino >= +0.5 / La Nina <= -0.5",
    )
    if r and r.status_code == 200:
        analyse_oni(r)

    # --- PRODUCT 2: SST Regional Indices ---
    r = fetch(
        "PRODUCT 2 — SST Regional Indices (Nino 1+2 / 3 / 4 / 3.4)",
        "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
        "Monthly SST and anomaly for all Nino regions; more granular than ONI alone",
    )
    if r and r.status_code == 200:
        analyse_sst_indices(r)

    # --- PRODUCT 3: Diagnostic Discussion ---
    r = fetch(
        "PRODUCT 3 — ENSO Diagnostic Discussion (monthly official text)",
        "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.txt",
        "Updated monthly; includes current ENSO status, ONI, and 3-month forecast narrative",
    )
    if r and r.status_code == 200:
        analyse_discussion(r, max_chars=5000)

    # --- PRODUCT 4: RONI Probabilities (9-season horizon) ---
    r = fetch(
        "PRODUCT 4 — RONI Probabilities (9 estacoes moveis: AMJ … DJF)",
        "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities/",
        "Tabela La Nina / Neutral / El Nino por estacao; referenciado internamente na Discussion",
    )
    if r and r.status_code == 200:
        analyse_roni_probabilities(r)
    elif r:
        print(f"  => HTTP {r.status_code} — endpoint nao disponivel")

    print(f"\n{SEP}")
    print("  PROBE NOAA CPC COMPLETO")
    print(SEP)


if __name__ == "__main__":
    main()

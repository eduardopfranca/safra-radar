"""
USDA API Discovery Probe
Goal: identify attribute IDs, commodity codes, country codes, and statisticcat
      values needed for Phase 1 data extraction.

Run from project root:
    python scripts/probe_usda_discovery.py
"""

import os
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _display_url(base: str, params: dict) -> str:
    """URL with query params but without auth keys."""
    safe = {k: v for k, v in params.items() if k not in ("api_key", "key")}
    return f"{base}?{urlencode(safe)}" if safe else base


def get_fas(url: str, fas_key: str, params: dict | None = None) -> dict | list | None:
    all_params = {"api_key": fas_key, **(params or {})}
    print(f"  URL : {_display_url(url, all_params)}  [auth=api_key]")
    t0 = time.perf_counter()
    try:
        r = requests.get(url, params=all_params, headers={"Accept": "application/json"}, timeout=30)
        elapsed = time.perf_counter() - t0
        print(f"  HTTP: {r.status_code}  latency={elapsed:.2f}s")
        if r.status_code == 200:
            return r.json()
        print(f"  Body: {r.text[:400]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def get_nass(url: str, nass_key: str, params: dict | None = None) -> list | None:
    all_params = {"key": nass_key, "format": "JSON", **(params or {})}
    print(f"  URL : {_display_url(url, all_params)}  [auth=key]")
    t0 = time.perf_counter()
    try:
        r = requests.get(url, params=all_params, timeout=60)
        elapsed = time.perf_counter() - t0
        print(f"  HTTP: {r.status_code}  latency={elapsed:.2f}s")
        if r.status_code == 200:
            payload = r.json()
            return payload.get("data", []) if isinstance(payload, dict) else payload
        print(f"  Body: {r.text[:400]}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def header(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def subheader(title: str) -> None:
    print(f"\n--- {title} ---")


# ---------------------------------------------------------------------------
# Probe 1 — FAS PSD attribute universe
# ---------------------------------------------------------------------------

def probe1_fas_attributes(fas_key: str) -> dict[int, str]:
    """Discover all attribute IDs from FAS PSD for Corn and Soybeans / Brazil 2025."""
    header("PROBE 1 — FAS PSD: Attribute Universe (Brazil 2025)")

    FAS_BASE = "https://api.fas.usda.gov/api/psd"
    KNOWN_IDS = {28: "Production", 176: "Ending Stocks", 88: "Exports", 4: "Area Harvested"}
    TARGET_KEYWORDS = {"total supply", "domestic consumption", "yield", "imports", "crush"}

    all_attrs: dict[int, str] = {}

    for comm_name, comm_code in [("Corn", "0440000"), ("Soybeans", "2222000")]:
        subheader(f"{comm_name} (commodityCode={comm_code}), Brazil (BR), year=2025")
        url = f"{FAS_BASE}/commodity/{comm_code}/country/BR/year/2025"
        data = get_fas(url, fas_key)

        if not data:
            print("  [NO DATA RETURNED]")
            continue

        print(f"\n  Records returned: {len(data)}")
        print(f"\n  {'attrId':>7}  {'attributeName':<45}  {'value':>14}  unitDescription")
        print(f"  {'-'*7}  {'-'*45}  {'-'*14}  {'-'*20}")

        for rec in sorted(data, key=lambda r: r.get("attributeId") or 0):
            attr_id   = rec.get("attributeId")
            attr_name = rec.get("attributeName", "")
            value     = rec.get("value", "")
            unit      = rec.get("unitDescription", "")
            flags = ""
            if attr_id in KNOWN_IDS:
                flags += " [KNOWN]"
            if any(t in attr_name.lower() for t in TARGET_KEYWORDS):
                flags += " *** TARGET ***"
            print(f"  {str(attr_id):>7}  {attr_name:<45}  {str(value):>14}  {unit}{flags}")
            if attr_id is not None:
                all_attrs[attr_id] = attr_name

    return all_attrs


# ---------------------------------------------------------------------------
# Probe 2 — FAS PSD commodity codes for Soybean Meal and Soybean Oil
# ---------------------------------------------------------------------------

def probe2_fas_commodities(fas_key: str) -> dict[str, str]:
    """Find PSD commodity codes for Soybean Meal and Soybean Oil."""
    header("PROBE 2 — FAS PSD: Soybean Meal & Soybean Oil Commodity Codes")

    FAS_BASE = "https://api.fas.usda.gov/api/psd"
    confirmed: dict[str, str] = {}

    subheader("Attempt 1: /commodities list endpoint")
    url_list = f"{FAS_BASE}/commodities"
    data = get_fas(url_list, fas_key)

    if data and isinstance(data, list):
        print(f"  Total commodities in list: {len(data)}")
        print("\n  Entries containing 'soy' (case-insensitive):")
        for c in data:
            name = c.get("commodityName", "")
            code = c.get("commodityCode", "")
            if "soy" in name.lower():
                print(f"    code={code!r:<12}  name={name!r}")
                confirmed[code] = name
        if not confirmed:
            print("  No 'soy' matches found in list.")
    else:
        print("  /commodities endpoint unavailable or unexpected format.")

    subheader("Attempt 2: probe candidate codes directly (Corn 2025 / Brazil as a known reference)")
    # ESR uses 901/902; PSD standard codes for soy derivatives
    candidates = {
        "2222100": "Soybean Meal (standard PSD candidate)",
        "2222200": "Soybean Oil (standard PSD candidate)",
        "0813100": "Soybean Meal (alt PSD candidate)",
        "0813200": "Soybean Oil (alt PSD candidate)",
    }
    for code, label in candidates.items():
        if code in confirmed:
            print(f"  code={code!r}: already confirmed via list — skipping direct probe")
            continue
        url_c = f"{FAS_BASE}/commodity/{code}/country/BR/year/2025"
        d = get_fas(url_c, fas_key)
        if d:
            comm_name = d[0].get("commodityName", "?") if d else "?"
            print(f"  code={code!r}: {len(d)} records  commodityName={comm_name!r}  *** HIT ***")
            confirmed[code] = comm_name
        else:
            print(f"  code={code!r} ({label}): no data")

    return confirmed


# ---------------------------------------------------------------------------
# Probe 3 — FAS PSD country codes for EU-27 and World aggregate
# ---------------------------------------------------------------------------

def probe3_fas_countries(fas_key: str) -> dict[str, str]:
    """Find PSD country codes for EU-27 and World aggregate."""
    header("PROBE 3 — FAS PSD: EU-27 and World Country Codes")

    FAS_BASE = "https://api.fas.usda.gov/api/psd"
    confirmed: dict[str, str] = {}

    subheader("Attempt 1: /countries list endpoint")
    url_list = f"{FAS_BASE}/countries"
    data = get_fas(url_list, fas_key)

    if data and isinstance(data, list):
        print(f"  Total countries in list: {len(data)}")
        print("\n  Entries matching 'eu', 'european', 'world', 'global', 'total':")
        for c in data:
            name = c.get("countryName", "")
            code = c.get("countryCode", "")
            if any(k in name.lower() for k in ("eu", "european", "world", "global", "total")):
                print(f"    code={code!r:<6}  name={name!r}")
                confirmed[code] = name
        if not confirmed:
            print("  No EU/World entries found in list — trying direct probes.")
    else:
        print("  /countries endpoint unavailable or unexpected format.")

    subheader("Attempt 2: probe candidate codes directly (Corn 0440000 / year 2025)")
    candidates = ["E2", "EU", "EC", "R0", "00", "WL"]
    for code in candidates:
        if code in confirmed:
            print(f"  code={code!r}: already confirmed via list — skipping")
            continue
        url_c = f"{FAS_BASE}/commodity/0440000/country/{code}/year/2025"
        d = get_fas(url_c, fas_key)
        if d:
            country_name = d[0].get("countryName", "?") if d else "?"
            print(f"  code={code!r}: {len(d)} records  countryName={country_name!r}  *** HIT ***")
            confirmed[code] = country_name
        else:
            print(f"  code={code!r}: no data")

    return confirmed


# ---------------------------------------------------------------------------
# Probe 4 — NASS statisticcat_desc universe
# ---------------------------------------------------------------------------

NASS_URL = "https://quickstats.nass.usda.gov/api/api_GET"

# Explicit fallback categories to probe if the unconstrained query is rejected
_NASS_CANDIDATE_CATS = [
    "AREA HARVESTED", "AREA PLANTED", "CONDITION", "PRICE RECEIVED",
    "PRODUCTION", "PROGRESS", "SALES", "STOCKS", "YIELD",
]


def probe4_nass_categories(nass_key: str) -> dict[str, list[str]]:
    """Discover all statisticcat_desc values for CORN and SOYBEANS, year=2024, NATIONAL."""
    header("PROBE 4 — NASS Quick Stats: statisticcat_desc Universe")

    discovered: dict[str, list[str]] = {}

    for commodity in ["CORN", "SOYBEANS"]:
        subheader(f"{commodity}, year=2024, agg_level_desc=NATIONAL (no statisticcat filter)")
        params = {
            "commodity_desc": commodity,
            "agg_level_desc": "NATIONAL",
            "year": "2024",
        }
        data = get_nass(NASS_URL, nass_key, params)

        if data is None:
            print("  [FAILED] — likely hit record limit (>50 000). Probing explicit categories:")
            found: list[str] = []
            for cat in _NASS_CANDIDATE_CATS:
                cat_params = {**params, "statisticcat_desc": cat}
                cat_data = get_nass(NASS_URL, nass_key, cat_params)
                if cat_data is not None:
                    print(f"    {cat:<30}  {len(cat_data)} records  *** EXISTS ***")
                    found.append(cat)
                else:
                    print(f"    {cat:<30}  no data / error")
            discovered[commodity] = found
            continue

        print(f"  Records returned: {len(data)}")
        cats = sorted(set(r.get("statisticcat_desc", "") for r in data if r.get("statisticcat_desc")))
        discovered[commodity] = cats

        print(f"\n  Unique statisticcat_desc values ({len(cats)}):")
        NOTES = {
            "STOCKS":   "← used in get_national_stocks",
            "PROGRESS": "← used in get_crop_progress",
            "CONDITION":"← target for crop condition feature",
        }
        for cat in cats:
            count = sum(1 for r in data if r.get("statisticcat_desc") == cat)
            note  = NOTES.get(cat, "")
            print(f"    {cat:<30}  ({count:>5} records)  {note}")

    return discovered


# ---------------------------------------------------------------------------
# Probe 5 — NASS crop condition short_desc patterns
# ---------------------------------------------------------------------------

def probe5_nass_condition(nass_key: str, categories_map: dict[str, list[str]]) -> list[str]:
    """Discover short_desc patterns for crop condition data (CORN, 2024, NATIONAL)."""
    header("PROBE 5 — NASS Quick Stats: Crop Condition short_desc Patterns")

    corn_cats = categories_map.get("CORN", [])
    condition_cat = next((c for c in corn_cats if "condition" in c.lower()), "CONDITION")
    print(f"  Using statisticcat_desc={condition_cat!r}  (derived from Probe 4)")

    subheader(f"CORN, year=2024, statisticcat_desc={condition_cat!r}, agg_level_desc=NATIONAL")
    params = {
        "commodity_desc": "CORN",
        "statisticcat_desc": condition_cat,
        "agg_level_desc": "NATIONAL",
        "year": "2024",
    }
    data = get_nass(NASS_URL, nass_key, params)

    if data is None:
        print("  [FAILED]")
        return []

    print(f"  Records returned: {len(data)}")

    short_descs = sorted(set(r.get("short_desc", "") for r in data if r.get("short_desc")))
    print(f"\n  Unique short_desc values ({len(short_descs)}):")
    for sd in short_descs:
        print(f"    {sd}")

    # Show one example record (non-empty fields only)
    if data:
        subheader("Example record (non-empty fields only)")
        for k, v in data[0].items():
            if v and str(v).strip():
                print(f"    {k:<30}: {v}")

    return short_descs


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(
    p1_attrs: dict[int, str],
    p2_commodities: dict[str, str],
    p3_countries: dict[str, str],
    p4_categories: dict[str, list[str]],
    p5_short_descs: list[str],
) -> None:
    header("SUMMARY")

    KNOWN_ATTRS = {28: "Production", 176: "Ending Stocks", 88: "Exports", 4: "Area Harvested"}

    print("\n[1] FAS PSD — All Attribute IDs (merged from Corn + Soybeans / Brazil 2025):")
    if p1_attrs:
        for attr_id, attr_name in sorted(p1_attrs.items()):
            tag = "  [previously known]" if attr_id in KNOWN_ATTRS else "  [NEW]"
            print(f"      {attr_id:>6}  {attr_name}{tag}")
    else:
        print("      No attributes collected — check Probe 1 output above.")

    print("\n[2] FAS PSD — Soybean Meal / Soybean Oil Commodity Codes:")
    if p2_commodities:
        for code, name in p2_commodities.items():
            print(f"      code={code!r:<12}  name={name!r}")
    else:
        print("      Could not confirm any codes — check Probe 2 output above.")

    print("\n[3] FAS PSD — EU-27 / World Country Codes Confirmed:")
    if p3_countries:
        for code, name in p3_countries.items():
            print(f"      code={code!r:<6}  name={name!r}")
    else:
        print("      No candidate codes returned data — check Probe 3 output above.")

    print("\n[4] NASS — statisticcat_desc Values Discovered:")
    for commodity, cats in p4_categories.items():
        print(f"    {commodity}:")
        NOTES = {
            "STOCKS":   "← used in get_national_stocks",
            "PROGRESS": "← used in get_crop_progress",
            "CONDITION":"← target for crop condition feature",
        }
        for cat in cats:
            note = f"  {NOTES[cat]}" if cat in NOTES else ""
            print(f"        {cat}{note}")

    print("\n[5] NASS — Crop Condition short_desc Patterns (CORN 2024 NATIONAL):")
    if p5_short_descs:
        for sd in p5_short_descs:
            print(f"      {sd}")
    else:
        print("      No data returned from Probe 5.")

    print()
    print("  Flagging anything worth noting:")
    if not p2_commodities:
        print("  ! Probe 2: Soybean Meal / Oil codes unconfirmed.")
    if not p3_countries:
        print("  ! Probe 3: EU-27 / World codes unconfirmed — these are needed for global balance sheets.")
    if not p5_short_descs:
        print("  ! Probe 5: Crop condition data missing — verify statisticcat_desc name.")
    if p1_attrs:
        new_attrs = {k: v for k, v in p1_attrs.items() if k not in KNOWN_ATTRS}
        if new_attrs:
            print(f"  + Probe 1 found {len(new_attrs)} new attribute IDs not previously mapped in USDAFasClient.")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv()
    fas_key  = os.getenv("FAS_API_KEY")
    nass_key = os.getenv("USDA_API_KEY")

    missing = [name for name, val in [("FAS_API_KEY", fas_key), ("USDA_API_KEY", nass_key)] if not val]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}")
        print("Add them to .env and retry.")
        return

    print("=" * 70)
    print("  USDA API Discovery Probe")
    print("  Runs 5 probes across FAS PSD and NASS Quick Stats.")
    print("  API keys are never printed.")
    print("=" * 70)

    p1 = probe1_fas_attributes(fas_key)
    p2 = probe2_fas_commodities(fas_key)
    p3 = probe3_fas_countries(fas_key)
    p4 = probe4_nass_categories(nass_key)
    p5 = probe5_nass_condition(nass_key, p4)

    print_summary(p1, p2, p3, p4, p5)


if __name__ == "__main__":
    main()

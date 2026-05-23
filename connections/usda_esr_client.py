import logging
from datetime import datetime

from dotenv import load_dotenv

try:
    from connections.usda_base_client import BaseUSDAClient
except ImportError:
    from usda_base_client import BaseUSDAClient

logger = logging.getLogger(__name__)


class USDAEsrClient(BaseUSDAClient):
    """Client for USDA Foreign Agricultural Service (FAS) - Export Sales Reporting (ESR) API."""

    SOURCE_NAME = "USDA FAS ESR"
    BASE_URL = "https://api.fas.usda.gov/api/esr"
    AUTH_METHOD = "header"
    AUTH_KEY_NAME = "X-Api-Key"
    ENV_VAR = "FAS_API_KEY"

    # Integer codes confirmed via probe_usda_esr.py
    COMMODITIES = {
        "Corn":         401,
        "Soybeans":     801,
        "Soybean Meal": 901,
        "Soybean Oil":  902,
    }

    # Named countries with confirmed codes; all others reachable via allCountries endpoint
    COUNTRIES = {
        "China": 5700,
    }

    # All ESR weekly export figures are reported in Metric Tons (unitId=1).
    UNIT_ID = 1
    UNIT_NAME = "Metric Tons"

    def get_weekly_exports(
        self,
        commodity: str,
        market_year: int,
        country: str | None = None,
    ) -> dict:
        """
        Fetches weekly export sales records for a commodity/market_year.

        country=None  → all countries (allCountries endpoint)
        country="China" → China only (countryCode endpoint)

        Returns a P06-wrapped list of raw API records.
        source_timestamp is set to the most recent weekEndingDate in the payload.
        Records absent from the API response (e.g., weeks not yet reported) are omitted.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(
                f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}"
            )
        if country is not None and country not in self.COUNTRIES:
            raise ValueError(
                f"Country '{country}' not supported. Named countries: {list(self.COUNTRIES.keys())}. "
                "Pass country=None to fetch all countries."
            )

        comm_code = self.COMMODITIES[commodity]

        if country is None:
            path = f"/exports/commodityCode/{comm_code}/allCountries/marketYear/{market_year}"
        else:
            country_code = self.COUNTRIES[country]
            path = f"/exports/commodityCode/{comm_code}/countryCode/{country_code}/marketYear/{market_year}"

        raw_data = self._request(path)

        source_timestamp = None
        if raw_data:
            dates = [r.get("weekEndingDate") for r in raw_data if r.get("weekEndingDate")]
            if dates:
                source_timestamp = max(dates)

        return self._wrap(
            raw_data,
            source_url=f"{self.BASE_URL}{path}",
            source_timestamp=source_timestamp,
        )

    def get_weekly_exports_series(
        self,
        commodity: str,
        years: list[int],
        country: str | None = None,
    ) -> dict:
        """
        Fetches weekly export records for multiple market years.

        Returns a P06-wrapped dict: {year_str: [records]}.
        source_timestamp is the most recent weekEndingDate across all years.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(
                f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}"
            )
        if country is not None and country not in self.COUNTRIES:
            raise ValueError(
                f"Country '{country}' not supported. Named countries: {list(self.COUNTRIES.keys())}. "
                "Pass country=None to fetch all countries."
            )

        comm_code = self.COMMODITIES[commodity]

        series: dict[str, list] = {}
        all_dates: list[str] = []

        for year in years:
            result = self.get_weekly_exports(commodity, year, country)
            series[str(year)] = result["data"]
            if result["source_timestamp"]:
                all_dates.append(result["source_timestamp"])

        if country is None:
            source_url = (
                f"{self.BASE_URL}/exports/commodityCode/{comm_code}/allCountries/marketYear/{{year}}"
                f" — {len(years)} call{'s' if len(years) != 1 else ''}"
                f" ({', '.join(str(y) for y in years)})"
            )
        else:
            country_code = self.COUNTRIES[country]
            source_url = (
                f"{self.BASE_URL}/exports/commodityCode/{comm_code}/countryCode/{country_code}/marketYear/{{year}}"
                f" — {len(years)} call{'s' if len(years) != 1 else ''}"
                f" ({', '.join(str(y) for y in years)})"
            )

        source_timestamp = max(all_dates) if all_dates else None
        return self._wrap(series, source_url=source_url, source_timestamp=source_timestamp)

    def list_commodities(self) -> dict:
        """
        Fetches the complete list of commodities exposed by the ESR API.
        Returns a P06-wrapped dict whose `data` is a list of {commodityCode, commodityName, unitId}.
        """
        path = "/commodities"
        raw_data = self._request(path)
        return self._wrap(raw_data, source_url=f"{self.BASE_URL}{path}", source_timestamp=None)

    def list_countries(self) -> dict:
        """
        Fetches the complete list of countries (importers) exposed by the ESR API.
        Returns a P06-wrapped dict whose `data` is a list of {countryCode, countryName, countryDescription, regionId, gencCode}.
        """
        path = "/countries"
        raw_data = self._request(path)
        return self._wrap(raw_data, source_url=f"{self.BASE_URL}{path}", source_timestamp=None)

    def get_latest_week(self, commodity: str, country: str | None = None) -> dict:
        """
        Returns the most recent weekly snapshot for the given commodity/country.

        Strategy:
        1. Try the current calendar year as the marketing year.
        2. If the response is empty, fall back to the previous year.
        3. From the resulting records, return only those whose weekEndingDate equals the maximum weekEndingDate.

        Returns P06-wrapped dict. `data` is a list of records (one per country if country=None,
        one record if country is set). `source_timestamp` is the weekEndingDate of the snapshot.
        Falls back to empty data with source_timestamp=None if both years return nothing.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(
                f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}"
            )
        if country is not None and country not in self.COUNTRIES:
            raise ValueError(
                f"Country '{country}' not supported. Named countries: {list(self.COUNTRIES.keys())}. "
                "Pass country=None to fetch all countries."
            )

        current_year = datetime.now().year

        for year in (current_year, current_year - 1):
            result = self.get_weekly_exports(commodity, year, country)
            records = result["data"]
            if not records:
                continue

            dates = [r.get("weekEndingDate") for r in records if r.get("weekEndingDate")]
            if not dates:
                continue
            latest_date = max(dates)

            snapshot = [r for r in records if r.get("weekEndingDate") == latest_date]
            return self._wrap(
                snapshot,
                source_url=result["source_url"],
                source_timestamp=latest_date,
            )

        comm_code = self.COMMODITIES[commodity]
        fallback_path = f"/exports/commodityCode/{comm_code}/allCountries/marketYear/{current_year}"
        return self._wrap([], source_url=f"{self.BASE_URL}{fallback_path}", source_timestamp=None)


if __name__ == "__main__":
    import sys as _sys
    import os as _os
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _root not in _sys.path:
        _sys.path.insert(0, _root)

    from utils import calculate_delta_pct

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()

    # --- Display helpers ---

    # Populated dynamically from list_countries() before first use
    COUNTRY_NAMES: dict[int, str] = {}

    def _fmt(v: float | None) -> str:
        if v is None:
            return "—"
        if abs(v - round(v)) < 0.005:
            return f"{round(v):,}"
        return f"{v:,.2f}"

    def _fmt_pct(pct: float | None) -> str:
        if pct is None:
            return "—"
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.2f}%"

    def _country_label(code: int | None) -> str:
        if code is None:
            return "Unknown"
        return COUNTRY_NAMES.get(int(code), f"Unknown ({code})")

    def _latest_by_country(records: list[dict]) -> list[dict]:
        """Returns one entry per country — the record with the most recent weekEndingDate."""
        seen: dict[int, dict] = {}
        for r in records:
            code = r.get("countryCode")
            date = r.get("weekEndingDate", "")
            if code not in seen or date > seen[code].get("weekEndingDate", ""):
                seen[code] = r
        return sorted(seen.values(), key=lambda r: r.get("accumulatedExports") or 0, reverse=True)

    def _recent_weeks(records: list[dict], n: int = 8) -> list[dict]:
        return sorted(records, key=lambda r: r.get("weekEndingDate", ""))[-n:]

    def print_top_countries(title: str, result: dict, top_n: int = 10) -> None:
        records = result["data"]
        by_country = _latest_by_country(records)
        shown = by_country[:top_n]

        W_C = 30
        W_V = 18
        line_len = W_C + W_V * 3 + 4

        print()
        print("=" * line_len)
        print(f"  {title}  (top {top_n} by accumulated, latest week)")
        print("=" * line_len)
        hdr = f"  {'Country':<{W_C}}  {'Accumulated':>{W_V}}  {'Outstanding':>{W_V}}  {'Net Sales (wk)':>{W_V}}"
        print(hdr)
        print(f"  {'-' * W_C}  {'-' * W_V}  {'-' * W_V}  {'-' * W_V}")
        for r in shown:
            name = _country_label(r.get("countryCode"))
            acc  = r.get("accumulatedExports") or 0
            out  = r.get("outstandingSales") or 0
            net  = r.get("currentMYNetSales") or 0
            week = (r.get("weekEndingDate") or "")[:10]
            print(f"  {name:<{W_C}}  {_fmt(acc):>{W_V}}  {_fmt(out):>{W_V}}  {_fmt(net):>{W_V}}  [{week}]")

        print()
        print(f"  Total records in payload : {len(records)}")
        print(f"  Source: {result['source']}  |  Fetched at: {result['fetched_at']}")
        print(f"  Source timestamp: {result['source_timestamp']}")

    def print_country_weeks(title: str, result: dict, n: int = 10) -> None:
        records = _recent_weeks(result["data"], n)

        W_D = 14
        W_V = 16
        line_len = W_D + W_V * 4 + 4

        print()
        print("=" * line_len)
        print(f"  {title}  (last {n} weeks)")
        print("=" * line_len)
        hdr = (
            f"  {'Week ending':<{W_D}}"
            f"  {'Weekly exports':>{W_V}}"
            f"  {'Accumulated':>{W_V}}"
            f"  {'Outstanding':>{W_V}}"
            f"  {'Net sales':>{W_V}}"
        )
        print(hdr)
        print(f"  {'-' * W_D}  {'-' * W_V}  {'-' * W_V}  {'-' * W_V}  {'-' * W_V}")
        for r in records:
            print(
                f"  {(r.get('weekEndingDate') or '?')[:10]:<{W_D}}"
                f"  {_fmt(r.get('weeklyExports')):>{W_V}}"
                f"  {_fmt(r.get('accumulatedExports')):>{W_V}}"
                f"  {_fmt(r.get('outstandingSales')):>{W_V}}"
                f"  {_fmt(r.get('currentMYNetSales')):>{W_V}}"
            )

        print()
        print(f"  Source: {result['source']}  |  Fetched at: {result['fetched_at']}")
        print(f"  Source timestamp: {result['source_timestamp']}")

    def print_series_accumulated(title: str, result: dict, years: list[int], country: str | None) -> None:
        """For each year, prints accumulated exports at the latest reported week."""
        series = result["data"]
        yrs = [str(y) for y in years]

        rows: dict[str, dict] = {}
        for yr in yrs:
            records = sorted(series.get(yr, []), key=lambda r: r.get("weekEndingDate", ""))
            if not records:
                rows[yr] = {"week": "—", "acc": None}
                continue
            last = records[-1]
            rows[yr] = {
                "week": last.get("weekEndingDate", "?"),
                "acc": last.get("accumulatedExports"),
            }

        W_L = 18
        W_V = 18
        line_len = W_L + W_V * 2 + 4

        print()
        print("=" * line_len)
        print(f"  {title}  — accumulated at latest week per year")
        print("=" * line_len)
        hdr = f"  {'Market year':<{W_L}}  {'Accumulated':>{W_V}}  {'YoY change':>{W_V}}"
        print(hdr)
        print(f"  {'-' * W_L}  {'-' * W_V}  {'-' * W_V}")

        for i, yr in enumerate(yrs):
            acc_c = rows[yr]["acc"]
            acc_p = rows[yrs[i + 1]]["acc"] if i + 1 < len(yrs) else None
            pct = calculate_delta_pct(acc_c, acc_p)
            week_display = (rows[yr]["week"] or "")[:10]
            print(
                f"  {yr:<{W_L}}"
                f"  {_fmt(acc_c):>{W_V}}"
                f"  {_fmt_pct(pct):>{W_V}}"
                f"  [{week_display}]"
            )

        print()
        print(f"  Source: {result['source']}  |  Fetched at: {result['fetched_at']}")
        print(f"  Source timestamp: {result['source_timestamp']}")

    # --- Tests ---

    try:
        client = USDAEsrClient()
        print("[OK] Client initialized.\n")

        # 0 — Metadata: list_commodities + list_countries
        comms_result = client.list_commodities()
        print(f"[list_commodities] {len(comms_result['data'])} commodities available:")
        for c in comms_result["data"]:
            print(f"  {c.get('commodityCode'):>5}  {c.get('commodityName')}")

        countries_result = client.list_countries()
        COUNTRY_NAMES.update({
            c["countryCode"]: c["countryName"].strip()
            for c in countries_result["data"]
        })
        print(f"\n[list_countries] {len(COUNTRY_NAMES)} countries loaded into label map")

        # 1 — Soybeans: all countries 2025
        r1 = client.get_weekly_exports("Soybeans", 2025)
        print_top_countries("SOYBEANS 2025 — All Countries", r1, top_n=10)

        # 2 — Soybeans: China 2025
        r2 = client.get_weekly_exports("Soybeans", 2025, "China")
        print_country_weeks("SOYBEANS 2025 — China", r2, n=10)

        # 3 — Corn: all countries 2025 (smoke test)
        r3 = client.get_weekly_exports("Corn", 2025)
        print_top_countries("CORN 2025 — All Countries", r3, top_n=5)

        # 4 — Soybeans: China series 2023-2025 (YoY)
        r4 = client.get_weekly_exports_series("Soybeans", [2025, 2024, 2023], "China")
        print_series_accumulated("SOYBEANS — China series 2023-2025", r4, [2025, 2024, 2023], "China")

        # 5 — Soybean Meal / Soybean Oil smoke test
        print()
        print("=" * 60)
        print("  SMOKE TEST — Soybean Meal & Soybean Oil (all countries 2025)")
        print("=" * 60)
        for comm in ["Soybean Meal", "Soybean Oil"]:
            r = client.get_weekly_exports(comm, 2025)
            recs = r["data"]
            top = _latest_by_country(recs)[:3]
            print(f"\n  {comm}: {len(recs)} records — top 3 by accumulated:")
            for row in top:
                name = _country_label(row.get("countryCode"))
                acc = row.get("accumulatedExports") or 0
                print(f"    {name}: {_fmt(acc)}")

        # 6 — Latest week
        print()
        print("=" * 60)
        print("  LATEST WEEK — Soybeans (all countries) & China only")
        print("=" * 60)

        latest_all = client.get_latest_week("Soybeans")
        latest_china = client.get_latest_week("Soybeans", "China")

        print(f"\n  Soybeans all countries — latest week: {latest_all['source_timestamp']}")
        print(f"  Records in snapshot: {len(latest_all['data'])}")

        print(f"\n  Soybeans China — latest week: {latest_china['source_timestamp']}")
        if latest_china["data"]:
            rec = latest_china["data"][0]
            print(f"    Weekly exports: {rec.get('weeklyExports'):,}")
            print(f"    Accumulated:    {rec.get('accumulatedExports'):,}")
            print(f"    Outstanding:    {rec.get('outstandingSales'):,}")

        # 7 — Error handling
        print()
        print("=" * 60)
        print("  ERROR HANDLING")
        print("=" * 60)
        try:
            client.get_weekly_exports("Corn", 2025, "Narnia")
        except ValueError as e:
            print(f"\n  [OK] Invalid country caught: {e}")

        try:
            client.get_weekly_exports("Coffee", 2025)
        except ValueError as e:
            print(f"  [OK] Invalid commodity caught: {e}")

    except Exception as e:
        print(f"\n[FAIL] Setup or execution failed: {e}")
        raise

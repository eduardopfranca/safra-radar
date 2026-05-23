import logging

from dotenv import load_dotenv

try:
    from connections.usda_base_client import BaseUSDAClient
except ImportError:
    from usda_base_client import BaseUSDAClient

logger = logging.getLogger(__name__)


class USDAFasClient(BaseUSDAClient):
    """Client for USDA Foreign Agricultural Service (FAS) - PSD Online API."""

    SOURCE_NAME = "USDA FAS PSD"
    BASE_URL = "https://api.fas.usda.gov/api/psd"
    AUTH_METHOD = "query_param"
    AUTH_KEY_NAME = "api_key"
    ENV_VAR = "FAS_API_KEY"

    COMMODITIES = {
        "Corn":         "0440000",
        "Soybeans":     "2222000",
        "Soybean Meal": "0813100",
        "Soybean Oil":  "4232000",
    }

    COUNTRIES = {
        "Brazil":    "BR",
        "China":     "CH",
        "US":        "US",
        "Argentina": "AR",
    }

    ATTRIBUTES = {
        1:   "Area Planted",
        4:   "Area Harvested",
        7:   "Crush",
        20:  "Beginning Stocks",
        28:  "Production",
        57:  "Imports",
        86:  "Total Supply",
        88:  "Exports",
        125: "Domestic Consumption",
        176: "Ending Stocks",
        184: "Yield",
        195: "Stocks-to-Use",
    }

    def get_country_balance(self, commodity: str, country: str, year: str) -> dict:
        """
        Fetches the balance sheet for a single commodity/country/year.

        Returns a P06-wrapped dict. Attributes absent from the API response are
        silently omitted — consumers must not assume every key is present.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")
        if country not in self.COUNTRIES:
            raise ValueError(f"Country '{country}' not supported. Allowed: {list(self.COUNTRIES.keys())}")

        comm_code = self.COMMODITIES[commodity]
        country_code = self.COUNTRIES[country]
        path = f"/commodity/{comm_code}/country/{country_code}/year/{year}"

        raw_data = self._request(path)

        balance_sheet: dict[str, float] = {}
        for item in raw_data:
            attr_id = item.get("attributeId")
            if attr_id in self.ATTRIBUTES:
                balance_sheet[self.ATTRIBUTES[attr_id]] = float(item.get("value", 0.0))

        return self._wrap(balance_sheet, source_url=f"{self.BASE_URL}{path}", source_timestamp=None)

    def get_country_balance_series(self, commodity: str, country: str, years: list[int]) -> dict:
        """
        Fetches balance sheets for multiple years in sequence.

        Returns a P06-wrapped dict where data maps year_str -> balance_sheet_dict.
        source_timestamp is the highest year in years (as a string).
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")
        if country not in self.COUNTRIES:
            raise ValueError(f"Country '{country}' not supported. Allowed: {list(self.COUNTRIES.keys())}")

        comm_code = self.COMMODITIES[commodity]
        country_code = self.COUNTRIES[country]

        series: dict[str, dict[str, float]] = {}
        for year in years:
            result = self.get_country_balance(commodity, country, str(year))
            series[str(year)] = result["data"]

        source_url = (
            f"{self.BASE_URL}/commodity/{comm_code}/country/{country_code}/year/{{year}}"
            f" — {len(years)} call{'s' if len(years) != 1 else ''}"
            f" ({', '.join(str(y) for y in years)})"
        )
        source_timestamp = str(max(years)) if years else None
        return self._wrap(series, source_url=source_url, source_timestamp=source_timestamp)


if __name__ == "__main__":
    import sys as _sys
    import os as _os
    # Ensure project root is importable when running this file directly
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _root not in _sys.path:
        _sys.path.insert(0, _root)

    from utils import calculate_delta_pct

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()

    # --- Display helpers ---

    def _fmt(v: float | None) -> str:
        """Format a value: integer if whole number, otherwise 2 decimal places."""
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

    def _safra(yr: str) -> str:
        y = int(yr)
        return f"Safra {y}/{str(y + 1)[2:]}"

    def print_series_table(title: str, result: dict, years: list[int]) -> None:
        series = result["data"]
        yrs = [str(y) for y in years]

        # Collect attribute names preserving order of first appearance
        all_attrs: list[str] = []
        seen: set[str] = set()
        for yr in yrs:
            for attr in series.get(yr, {}):
                if attr not in seen:
                    all_attrs.append(attr)
                    seen.add(attr)

        W_A = 22
        W_V = 16
        line_len = W_A + W_V * len(yrs) + 4

        print()
        print("=" * line_len)
        print(f"  {title}")
        print("=" * line_len)

        hdr = f"  {'':>{W_A}}"
        for yr in yrs:
            hdr += f"  {_safra(yr):>{W_V}}"
        print(hdr)
        print(f"  {'-' * W_A}" + "".join(f"  {'-' * W_V}" for _ in yrs))

        for attr in all_attrs:
            row = f"  {attr:<{W_A}}"
            for yr in yrs:
                v = series.get(yr, {}).get(attr)
                row += f"  {_fmt(v):>{W_V}}"
            print(row)

        for i in range(len(yrs) - 1):
            yr_c, yr_p = yrs[i], yrs[i + 1]
            print(f"\n  YoY Variation ({_safra(yr_c)} vs {_safra(yr_p)}):")
            any_delta = False
            for attr in all_attrs:
                c = series.get(yr_c, {}).get(attr)
                p = series.get(yr_p, {}).get(attr)
                pct = calculate_delta_pct(c, p)
                if pct is not None:
                    print(f"    {attr:<{W_A}}  {_fmt_pct(pct):>10}")
                    any_delta = True
            if not any_delta:
                print("    (no delta data available)")

        print()
        print(f"  Source:           {result['source']}")
        print(f"  Fetched at:       {result['fetched_at']}")
        print(f"  Source timestamp: {result['source_timestamp']}")

    # --- Tests ---

    try:
        client = USDAFasClient()
        print("[OK] Client initialized.\n")

        # 1 — Multi-year series: Corn / Brazil
        result = client.get_country_balance_series("Corn", "Brazil", [2025, 2024, 2023])
        print_series_table("BRAZIL — CORN", result, [2025, 2024, 2023])

        # 2 — Multi-year series: Soybeans / Brazil
        result = client.get_country_balance_series("Soybeans", "Brazil", [2025, 2024, 2023])
        print_series_table("BRAZIL — SOYBEANS", result, [2025, 2024, 2023])

        # 3 — Smoke test: new commodities resolve correctly
        print()
        print("=" * 60)
        print("  SMOKE TEST — Soybean Meal & Soybean Oil (Brazil 2025)")
        print("=" * 60)
        for comm in ["Soybean Meal", "Soybean Oil"]:
            r = client.get_country_balance(comm, "Brazil", "2025")
            print(f"\n  {comm}:")
            if r["data"]:
                for attr, val in list(r["data"].items())[:3]:
                    print(f"    {attr}: {_fmt(val)}")
            else:
                print("    [no mapped attributes returned by API]")

        # 4 — Error handling
        print()
        print("=" * 60)
        print("  ERROR HANDLING — invalid country")
        print("=" * 60)
        try:
            client.get_country_balance("Corn", "Narnia", "2025")
        except ValueError as e:
            print(f"\n  [OK] Caught expected error: {e}")

    except Exception as e:
        print(f"\n[FAIL] Setup or execution failed: {e}")

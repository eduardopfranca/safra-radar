import logging

from dotenv import load_dotenv

try:
    from connections.usda_base_client import BaseUSDAClient
except ImportError:
    from usda_base_client import BaseUSDAClient

logger = logging.getLogger(__name__)


class USDANassClient(BaseUSDAClient):
    """Client for USDA National Agricultural Statistics Service (NASS) - Quick Stats API."""

    SOURCE_NAME = "USDA NASS Quick Stats"
    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET"
    AUTH_METHOD = "query_param"
    AUTH_KEY_NAME = "key"
    ENV_VAR = "USDA_API_KEY"

    COMMODITIES = {
        "Corn": "CORN",
        "Soybeans": "SOYBEANS",
    }

    CONDITION_LEVELS = ["VERY POOR", "POOR", "FAIR", "GOOD", "EXCELLENT"]

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _nass_params(self, commodity: str, stat_cat: str, year: str) -> dict:
        return {
            "commodity_desc": self.COMMODITIES[commodity],
            "statisticcat_desc": stat_cat,
            "agg_level_desc": "NATIONAL",
            "year": year,
            "format": "JSON",
        }

    def _raw(self, params: dict) -> list:
        payload = self._request("", params)
        return payload.get("data", []) if isinstance(payload, dict) else []

    def _parse_float(self, item: dict) -> float | None:
        try:
            return float(str(item.get("Value", "0")).replace(",", "").strip())
        except ValueError:
            return None

    # -------------------------------------------------------------------------
    # Existing public methods (unchanged)
    # -------------------------------------------------------------------------

    def get_national_stocks(self, commodity: str, year: str) -> dict:
        """
        Fetches US national quarterly stocks for the given commodity and year.
        Returns a P06-wrapped dict with stocks mapped by reference period.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        raw_data = self._raw(self._nass_params(commodity, "STOCKS", year))

        stocks_by_quarter: dict[str, float] = {}
        for item in raw_data:
            short_desc = item.get("short_desc", "")
            if "ON FARM" in short_desc or "OFF FARM" in short_desc:
                continue
            if "STOCKS, MEASURED IN BU" in short_desc:
                period = item.get("reference_period_desc", "UNKNOWN")
                val = self._parse_float(item)
                if val is not None:
                    stocks_by_quarter[period] = val

        return self._wrap(stocks_by_quarter, source_url=self.BASE_URL, source_timestamp=None)

    def get_crop_progress(self, commodity: str, year: str) -> dict:
        """
        Fetches US weekly planting and harvesting progress.
        Returns a P06-wrapped dict keyed by week_ending date.
        Format: {'2025-05-18': {'planted': 65.0, 'harvested': 0.0}, ...}
        source_timestamp is the most recent week_ending with data.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        raw_data = self._raw(self._nass_params(commodity, "PROGRESS", year))

        progress_timeline: dict[str, dict[str, float]] = {}
        for item in raw_data:
            short_desc = item.get("short_desc", "")
            week_ending = item.get("week_ending")
            if not week_ending:
                continue
            if week_ending not in progress_timeline:
                progress_timeline[week_ending] = {"planted": 0.0, "harvested": 0.0}
            val = self._parse_float(item)
            if val is None:
                continue
            if "PCT PLANTED" in short_desc:
                progress_timeline[week_ending]["planted"] = val
            elif "PCT HARVESTED" in short_desc:
                progress_timeline[week_ending]["harvested"] = val

        source_timestamp = max(progress_timeline.keys()) if progress_timeline else None
        filtered = {k: v for k, v in sorted(progress_timeline.items()) if v["planted"] > 0 or v["harvested"] > 0}
        return self._wrap(filtered, source_url=self.BASE_URL, source_timestamp=source_timestamp)

    # -------------------------------------------------------------------------
    # New public methods — DEBT-01
    # -------------------------------------------------------------------------

    def get_crop_progress_series(self, commodity: str, years: list[str]) -> dict:
        """
        Fetches crop progress for multiple years.
        Returns a P06-wrapped dict: {year_str: {week_ending: {planted, harvested}}}.
        Useful for year-ago comparison and 5-year average computation in engines.
        source_timestamp is the most recent week_ending across all years.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        series: dict[str, dict] = {}
        all_timestamps: list[str] = []

        for year in years:
            result = self.get_crop_progress(commodity, year)
            series[year] = result["data"]
            if result["source_timestamp"]:
                all_timestamps.append(result["source_timestamp"])

        source_timestamp = max(all_timestamps) if all_timestamps else None
        return self._wrap(series, source_url=self.BASE_URL, source_timestamp=source_timestamp)

    def get_crop_condition(self, commodity: str, year: str) -> dict:
        """
        Fetches weekly US national crop condition for the given commodity and year.
        Returns a P06-wrapped dict: {week_ending: {"VERY POOR": float, ..., "EXCELLENT": float}}.
        Values are percentages (sum to ~100 for each week).
        source_timestamp is the most recent week_ending reported.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        raw_data = self._raw(self._nass_params(commodity, "CONDITION", year))

        condition_by_week: dict[str, dict[str, float]] = {}
        for item in raw_data:
            week_ending = item.get("week_ending")
            if not week_ending:
                continue
            short_desc = item.get("short_desc", "").upper()
            level = next((lvl for lvl in self.CONDITION_LEVELS if lvl in short_desc), None)
            if level is None:
                continue
            if week_ending not in condition_by_week:
                condition_by_week[week_ending] = {lvl: 0.0 for lvl in self.CONDITION_LEVELS}
            val = self._parse_float(item)
            if val is not None:
                condition_by_week[week_ending][level] = val

        source_timestamp = max(condition_by_week.keys()) if condition_by_week else None
        return self._wrap(
            dict(sorted(condition_by_week.items())),
            source_url=self.BASE_URL,
            source_timestamp=source_timestamp,
        )

    def get_crop_condition_series(self, commodity: str, years: list[str]) -> dict:
        """
        Fetches crop condition for multiple years.
        Returns a P06-wrapped dict: {year_str: {week_ending: {condition_levels}}}.
        Useful for year-ago comparison and 5-year average computation in engines.
        source_timestamp is the most recent week_ending across all years.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        series: dict[str, dict] = {}
        all_timestamps: list[str] = []

        for year in years:
            result = self.get_crop_condition(commodity, year)
            series[year] = result["data"]
            if result["source_timestamp"]:
                all_timestamps.append(result["source_timestamp"])

        source_timestamp = max(all_timestamps) if all_timestamps else None
        return self._wrap(series, source_url=self.BASE_URL, source_timestamp=source_timestamp)

    def get_acreage(self, commodity: str, year: str) -> dict:
        """
        Fetches US national planted and harvested acreage for the given commodity and year.
        Returns a P06-wrapped dict: {"planted_acres": float, "harvested_acres": float}.
        Makes two API calls (AREA PLANTED + AREA HARVESTED). source_timestamp is None (annual).
        Prefers the final annual survey record (reference_period_desc == "YEAR") over forecasts.
        NASS short_desc pattern: "{COMMODITY} - ACRES PLANTED / ACRES HARVESTED".
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        result: dict[str, float] = {}

        for stat_cat, key, acres_phrase in [
            ("AREA PLANTED",   "planted_acres",   "ACRES PLANTED"),
            ("AREA HARVESTED", "harvested_acres", "ACRES HARVESTED"),
        ]:
            raw_data = self._raw(self._nass_params(commodity, stat_cat, year))

            # Two-pass: prefer final annual figure, then accept any matching record
            for ref_pref in ("YEAR", None):
                for item in raw_data:
                    short_desc = item.get("short_desc", "").upper()
                    ref_period = item.get("reference_period_desc", "")
                    if acres_phrase not in short_desc:
                        continue
                    if ref_pref is not None and ref_period != ref_pref:
                        continue
                    val = self._parse_float(item)
                    if val and val > 0:
                        result[key] = val
                        break
                if key in result:
                    break

        return self._wrap(result, source_url=self.BASE_URL, source_timestamp=None)

    def get_yield(self, commodity: str, year: str) -> dict:
        """
        Fetches US national crop yield for the given commodity and year.
        Returns a P06-wrapped dict: {"yield_bu_per_acre": float}.
        For corn, prefers GRAIN records. source_timestamp is None (annual survey).
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        raw_data = self._raw(self._nass_params(commodity, "YIELD", year))

        result: dict[str, float] = {}
        for grain_only in (True, False):
            for item in raw_data:
                short_desc = item.get("short_desc", "").upper()
                if "BU / ACRE" not in short_desc:
                    continue
                if grain_only and "GRAIN" not in short_desc:
                    continue
                val = self._parse_float(item)
                if val and val > 0:
                    result["yield_bu_per_acre"] = val
                    break
            if result:
                break

        return self._wrap(result, source_url=self.BASE_URL, source_timestamp=None)

    def get_production(self, commodity: str, year: str) -> dict:
        """
        Fetches US national total production for the given commodity and year.
        Returns a P06-wrapped dict: {"production_bu": float}.
        For corn, prefers GRAIN records. source_timestamp is None (annual survey).
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        raw_data = self._raw(self._nass_params(commodity, "PRODUCTION", year))

        result: dict[str, float] = {}
        for grain_only in (True, False):
            for item in raw_data:
                short_desc = item.get("short_desc", "").upper()
                if "MEASURED IN BU" not in short_desc:
                    continue
                if grain_only and "GRAIN" not in short_desc:
                    continue
                val = self._parse_float(item)
                if val and val > 0:
                    result["production_bu"] = val
                    break
            if result:
                break

        return self._wrap(result, source_url=self.BASE_URL, source_timestamp=None)


if __name__ == "__main__":
    import sys as _sys
    import os as _os
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _root not in _sys.path:
        _sys.path.insert(0, _root)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv()

    # --- Display helpers ---

    def _fmt_i(v: float | None) -> str:
        return f"{v:,.0f}" if v is not None else "—"

    def _fmt_f(v: float | None, dec: int = 1) -> str:
        return f"{v:,.{dec}f}" if v is not None else "—"

    def _pct_bar(levels: dict) -> str:
        g = levels.get("GOOD", 0) or 0
        e = levels.get("EXCELLENT", 0) or 0
        return f"G+E={g + e:.0f}%  |  " + "  ".join(
            f"{lvl[:4]}={levels.get(lvl, 0):.0f}%" for lvl in ["VERY POOR", "POOR", "FAIR", "GOOD", "EXCELLENT"]
        )

    # --- Tests ---

    try:
        client = USDANassClient()
        print("[OK] Client initialized.\n")

        # 1 — Existing: Corn Stocks 2024
        print("=" * 60)
        print("  Test 1: US Corn Stocks (2024)")
        print("=" * 60)
        r = client.get_national_stocks("Corn", "2024")
        if r["data"]:
            for quarter, val in r["data"].items():
                print(f"  {quarter}: {_fmt_i(val)} BU")
        else:
            print("  [empty]")
        print(f"  source_timestamp: {r['source_timestamp']}")

        # 2 — Existing: Soybeans Progress 2025
        print()
        print("=" * 60)
        print("  Test 2: US Soybeans Crop Progress (2025) — last 4 weeks")
        print("=" * 60)
        r = client.get_crop_progress("Soybeans", "2025")
        weeks = list(r["data"].keys())
        for w in weeks[-4:]:
            d = r["data"][w]
            print(f"  {w}: Planted {_fmt_f(d['planted'])}%  Harvested {_fmt_f(d['harvested'])}%")
        print(f"  source_timestamp: {r['source_timestamp']}")

        # 3 — NEW: Progress series — Corn 2024 vs 2025
        print()
        print("=" * 60)
        print("  Test 3: Corn Progress Series (2024 vs 2025) — latest week each year")
        print("=" * 60)
        r = client.get_crop_progress_series("Corn", ["2025", "2024"])
        for yr in ["2025", "2024"]:
            weeks = r["data"].get(yr, {})
            if weeks:
                last_w = list(weeks.keys())[-1]
                d = weeks[last_w]
                print(f"  {yr} ({last_w}): Planted {_fmt_f(d['planted'])}%  Harvested {_fmt_f(d['harvested'])}%")
            else:
                print(f"  {yr}: no data")
        print(f"  source_timestamp: {r['source_timestamp']}")

        # 4 — NEW: Crop Condition — Corn 2025
        print()
        print("=" * 60)
        print("  Test 4: US Corn Crop Condition (2025) — last 3 weeks")
        print("=" * 60)
        r = client.get_crop_condition("Corn", "2025")
        weeks = list(r["data"].keys())
        if weeks:
            print(f"  Total weeks: {len(weeks)}")
            for w in weeks[-3:]:
                print(f"  {w}: {_pct_bar(r['data'][w])}")
        else:
            print("  [empty]")
        print(f"  source_timestamp: {r['source_timestamp']}")

        # 5 — NEW: Condition series — Corn 2023/2024/2025 (year-ago + 2-yr)
        print()
        print("=" * 60)
        print("  Test 5: Corn Condition Series (2023-2025) — Good+Excellent at latest week")
        print("=" * 60)
        r = client.get_crop_condition_series("Corn", ["2025", "2024", "2023"])
        for yr in ["2025", "2024", "2023"]:
            weeks = r["data"].get(yr, {})
            if weeks:
                last_w = list(weeks.keys())[-1]
                cond = weeks[last_w]
                ge = (cond.get("GOOD") or 0) + (cond.get("EXCELLENT") or 0)
                print(f"  {yr} ({last_w}): Good+Excellent = {ge:.0f}%")
            else:
                print(f"  {yr}: no data")
        print(f"  source_timestamp: {r['source_timestamp']}")

        # 6 — NEW: Acreage — Corn and Soybeans 2025
        print()
        print("=" * 60)
        print("  Test 6: US Acreage (2025)")
        print("=" * 60)
        for comm in ["Corn", "Soybeans"]:
            r = client.get_acreage(comm, "2025")
            d = r["data"]
            planted = d.get("planted_acres")
            harvested = d.get("harvested_acres")
            print(f"  {comm}: planted={_fmt_i(planted)} ac  harvested={_fmt_i(harvested)} ac")

        # 7 — NEW: Yield — Corn and Soybeans 2025
        print()
        print("=" * 60)
        print("  Test 7: US Yield (2025)")
        print("=" * 60)
        for comm in ["Corn", "Soybeans"]:
            r = client.get_yield(comm, "2025")
            val = r["data"].get("yield_bu_per_acre")
            print(f"  {comm}: {_fmt_f(val, 1)} BU/ACRE")

        # 8 — NEW: Production — Corn and Soybeans 2025
        print()
        print("=" * 60)
        print("  Test 8: US Production (2025)")
        print("=" * 60)
        for comm in ["Corn", "Soybeans"]:
            r = client.get_production(comm, "2025")
            val = r["data"].get("production_bu")
            print(f"  {comm}: {_fmt_i(val)} BU")

        # 9 — Error handling
        print()
        print("=" * 60)
        print("  Test 9: Error Handling")
        print("=" * 60)
        try:
            client.get_crop_condition("Wheat", "2025")
        except ValueError as e:
            print(f"  [OK] Invalid commodity caught: {e}")

    except Exception as e:
        print(f"\n[FAIL] Setup or execution failed: {e}")
        raise

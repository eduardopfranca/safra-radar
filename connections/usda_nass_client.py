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

    def get_national_stocks(self, commodity: str, year: str) -> dict:
        """
        Fetches US national quarterly stocks for the given commodity and year.
        Returns a P06-wrapped dict with stocks mapped by reference period.
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported. Allowed: {list(self.COMMODITIES.keys())}")

        params = {
            "commodity_desc": self.COMMODITIES[commodity],
            "statisticcat_desc": "STOCKS",
            "agg_level_desc": "NATIONAL",
            "year": year,
            "format": "JSON",
        }

        payload = self._request("", params)
        raw_data = payload.get("data", []) if isinstance(payload, dict) else []

        stocks_by_quarter: dict[str, float] = {}
        for item in raw_data:
            short_desc = item.get("short_desc", "")
            if "ON FARM" in short_desc or "OFF FARM" in short_desc:
                continue
            if "STOCKS, MEASURED IN BU" in short_desc:
                period = item.get("reference_period_desc", "UNKNOWN")
                raw_value = item.get("Value", "0")
                try:
                    stocks_by_quarter[period] = float(str(raw_value).replace(",", "").strip())
                except ValueError:
                    continue

        return self._wrap(stocks_by_quarter, source_url=self.BASE_URL, source_timestamp=None)

    def get_crop_progress(self, commodity: str, year: str) -> dict:
        """
        Fetches US planting and harvesting progress.
        Returns a P06-wrapped dict with chronological progress keyed by week_ending date.
        Format of data: {'2025-05-18': {'planted': 65.0, 'harvested': 0.0}, ...}
        """
        if commodity not in self.COMMODITIES:
            raise ValueError(f"Commodity '{commodity}' not supported.")

        params = {
            "commodity_desc": self.COMMODITIES[commodity],
            "statisticcat_desc": "PROGRESS",
            "agg_level_desc": "NATIONAL",
            "year": year,
            "format": "JSON",
        }

        payload = self._request("", params)
        raw_data = payload.get("data", []) if isinstance(payload, dict) else []

        progress_timeline: dict[str, dict[str, float]] = {}
        for item in raw_data:
            short_desc = item.get("short_desc", "")
            week_ending = item.get("week_ending")
            if not week_ending:
                continue
            if week_ending not in progress_timeline:
                progress_timeline[week_ending] = {"planted": 0.0, "harvested": 0.0}
            try:
                clean_value = float(str(item.get("Value", "0")).replace(",", "").strip())
            except ValueError:
                continue
            if "PCT PLANTED" in short_desc:
                progress_timeline[week_ending]["planted"] = clean_value
            elif "PCT HARVESTED" in short_desc:
                progress_timeline[week_ending]["harvested"] = clean_value

        source_timestamp = max(progress_timeline.keys()) if progress_timeline else None
        filtered = {k: v for k, v in sorted(progress_timeline.items()) if v["planted"] > 0 or v["harvested"] > 0}
        return self._wrap(filtered, source_url=self.BASE_URL, source_timestamp=source_timestamp)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("=" * 60)
    print("Testing USDANassClient Connection")
    print("=" * 60)

    load_dotenv()

    try:
        client = USDANassClient()
        print("[OK] Client initialized successfully.")

        print("\n--- Test 1: US Corn Stocks (2024) ---")
        result = client.get_national_stocks("Corn", "2024")
        if result["data"]:
            for quarter, value in result["data"].items():
                print(f"  {quarter}: {value:,.0f} Bushels")
        else:
            print("  No stocks data found for this year.")

        print("\n--- Test 2: US Soybeans Crop Progress (2025) ---")
        result = client.get_crop_progress("Soybeans", "2025")
        if result["data"]:
            latest_weeks = list(result["data"].keys())[-3:]
            for week in latest_weeks:
                data = result["data"][week]
                print(f"  Week Ending {week}: Planted {data['planted']}% | Harvested {data['harvested']}%")
        else:
            print("  No progress data found yet for this year.")

    except Exception as e:
        print(f"[FAIL] Setup or execution failed: {e}")

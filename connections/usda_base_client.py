import os
import logging
import time
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BaseUSDAClient:
    """Base class for USDA API clients. Subclasses override the class-level attributes."""

    SOURCE_NAME: str = ""
    BASE_URL: str = ""
    AUTH_METHOD: str = "header"   # "header" or "query_param"
    AUTH_KEY_NAME: str = "X-Api-Key"
    ENV_VAR: str = ""

    def __init__(self, api_key: str | None = None, timeout: int = 15) -> None:
        resolved_key = api_key or os.getenv(self.ENV_VAR)
        if not resolved_key:
            raise ValueError(f"{self.ENV_VAR} is required but was not found.")
        self._api_key = resolved_key
        self.timeout = timeout

        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        if self.AUTH_METHOD == "header":
            self.session.headers[self.AUTH_KEY_NAME] = self._api_key

    def _request(self, path: str, params: dict | None = None) -> dict | list:
        url = f"{self.BASE_URL}{path}"
        req_params = dict(params) if params else {}

        if self.AUTH_METHOD == "query_param":
            req_params[self.AUTH_KEY_NAME] = self._api_key

        logger.info("GET %s", url)
        start = time.perf_counter()
        try:
            response = self.session.get(url, params=req_params, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("Request failed: %s", e)
            raise
        latency = time.perf_counter() - start
        logger.info("Response in %.2fs — status %s", latency, response.status_code)
        return response.json()

    def _wrap(self, data: Any, source_url: str, source_timestamp: str | None = None) -> dict:
        return {
            "data": data,
            "source": self.SOURCE_NAME,
            "source_url": source_url,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_timestamp": source_timestamp,
        }

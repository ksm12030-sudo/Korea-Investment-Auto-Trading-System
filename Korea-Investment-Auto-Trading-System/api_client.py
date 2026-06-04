from typing import Any, Dict, Optional

import requests

from config import APP_KEY, APP_SECRET, BASE_URL
from logger import get_logger


logger = get_logger(__name__)


class KisApiClient:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def _headers(self, tr_id: str) -> Dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": APP_KEY or "",
            "appsecret": APP_SECRET or "",
            "tr_id": tr_id,
        }

    def get(
        self,
        path: str,
        tr_id: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"

        try:
            response = requests.get(
                url,
                headers=self._headers(tr_id),
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"GET request failed: {url} | {e}")
            raise

    def post(
        self,
        path: str,
        tr_id: str,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"

        try:
            response = requests.post(
                url,
                headers=self._headers(tr_id),
                json=json_body,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"POST request failed: {url} | {e}")
            raise
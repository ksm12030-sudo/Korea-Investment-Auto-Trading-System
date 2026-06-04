import json
from datetime import date
from pathlib import Path
from typing import Optional

import requests

from config import APP_KEY, APP_SECRET, BASE_URL
from logger import get_logger


TOKEN_CACHE_FILE = Path("token_cache.json")
logger = get_logger(__name__)


def load_cached_token() -> Optional[str]:
    if not TOKEN_CACHE_FILE.exists():
        return None

    try:
        with TOKEN_CACHE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("date") == date.today().isoformat():
            logger.info("Reusing cached access token")
            return data.get("access_token")

    except Exception as e:
        logger.warning(f"Failed to load cached token: {e}")

    return None


def save_token(access_token: str) -> None:
    data = {
        "date": date.today().isoformat(),
        "access_token": access_token,
    }

    with TOKEN_CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("Saved new access token to token_cache.json")


def issue_new_token() -> str:
    if not APP_KEY or not APP_SECRET:
        raise ValueError("APP_KEY or APP_SECRET is missing")

    url = f"{BASE_URL}/oauth2/tokenP"

    headers = {
        "content-type": "application/json",
    }

    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    logger.info("Requesting new access token")

    response = requests.post(url, headers=headers, json=body, timeout=10)
    response.raise_for_status()

    data = response.json()

    access_token = data.get("access_token")

    if not access_token:
        raise RuntimeError(f"access_token not found in response: {data}")

    save_token(access_token)
    return access_token


def get_access_token() -> str:
    cached_token = load_cached_token()

    if cached_token:
        return cached_token

    return issue_new_token()
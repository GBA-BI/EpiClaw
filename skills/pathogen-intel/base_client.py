"""Base HTTP client with rate-limiting, disk caching, and retry for EpiClaw connectors."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests


class BaseAPIClient:
    """Rate-limited, caching HTTP client for public health REST APIs.

    Features:
        - Per-API rate limiting (configurable interval between requests)
        - 24-hour disk cache (SHA-256 keyed)
        - Automatic retry on HTTP 429 (rate limit exceeded)
        - Configurable timeout
    """

    def __init__(
        self,
        base_url: str,
        cache_dir: Path | None = None,
        rate_limit: float = 0.5,
        use_cache: bool = True,
        cache_ttl: int = 86400,
        timeout: int = 30,
        user_agent: str = "EpiClaw/0.1.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.rate_limit = rate_limit  # seconds between requests
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self._last_request = 0.0

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})

        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = Path.home() / ".epiclaw" / "cache"
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, method: str, url: str, params: dict | None, body: Any) -> str:
        """Generate SHA-256 cache key from request parameters."""
        raw = f"{method}|{url}|{json.dumps(params, sort_keys=True)}|{json.dumps(body, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _read_cache(self, key: str) -> dict | None:
        """Read cached response if fresh."""
        if not self.use_cache:
            return None
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - data.get("_cached_at", 0) < self.cache_ttl:
                return data.get("_payload")
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def _write_cache(self, key: str, payload: Any) -> None:
        """Write response to cache."""
        if not self.use_cache:
            return
        path = self.cache_dir / f"{key}.json"
        data = {"_cached_at": time.time(), "_payload": payload}
        path.write_text(json.dumps(data, default=str), encoding="utf-8")

    def _throttle(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()

    def get(self, endpoint: str, params: dict | None = None) -> Any:
        """HTTP GET with rate-limiting, caching, and retry on 429."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        cache_key = self._cache_key("GET", url, params, None)

        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        self._throttle()
        max_retries = 3
        for attempt in range(max_retries):
            resp = self._session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 429:
                wait = min(2 ** attempt * 2, 30)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            try:
                payload = resp.json()
            except requests.exceptions.JSONDecodeError:
                payload = {"_text": resp.text}
            self._write_cache(cache_key, payload)
            return payload

        raise requests.exceptions.HTTPError(f"Rate limited after {max_retries} retries: {url}")

    def post(self, endpoint: str, json_body: dict | None = None) -> Any:
        """HTTP POST with rate-limiting, caching, and retry on 429."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        cache_key = self._cache_key("POST", url, None, json_body)

        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        self._throttle()
        max_retries = 3
        for attempt in range(max_retries):
            resp = self._session.post(url, json=json_body, timeout=self.timeout)
            if resp.status_code == 429:
                wait = min(2 ** attempt * 2, 30)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            try:
                payload = resp.json()
            except requests.exceptions.JSONDecodeError:
                payload = {"_text": resp.text}
            self._write_cache(cache_key, payload)
            return payload

        raise requests.exceptions.HTTPError(f"Rate limited after {max_retries} retries: {url}")

    def get_text(self, endpoint: str, params: dict | None = None) -> str:
        """HTTP GET returning raw text (for XML, FASTA, etc.)."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        self._throttle()
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from typing import Any

import httpx

from .config import ProjectConfig, Settings


class PolarionError(RuntimeError):
    def __init__(self, status_code: int, message: str, details: Any = None):
        super().__init__(f"Polarion API returned {status_code}: {message}")
        self.status_code, self.message, self.details = status_code, message, details


class PolarionClient:
    def __init__(self, settings: Settings, project: ProjectConfig | None = None,
                 http: httpx.AsyncClient | None = None):
        self.settings = settings
        self.project = project or settings.selected_project()
        self._http = http
        self._owns_http = http is None

    async def __aenter__(self) -> "PolarionClient":
        if self._http is None:
            s = self.project.session_config
            password = os.getenv("POLARION_PASSWORD") or s.password
            self._http = httpx.AsyncClient(
                base_url=s.server_url.rstrip("/") + "/polarion/rest/v1",
                auth=(s.username, password) if s.username and password else None,
                headers={"Accept": "application/json"}, verify=self.settings.verify_tls,
                timeout=s.timeout_seconds, follow_redirects=True)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_http and self._http:
            await self._http.aclose()

    async def request(self, method: str, path: str, *, params: Mapping[str, Any] | None = None,
                      json: Any = None) -> Any:
        if self._http is None:
            raise RuntimeError("PolarionClient must be used as an async context manager")
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = await self._http.request(method, path, params=params, json=json)
                if response.status_code in {429, 502, 503, 504} and attempt < self.settings.max_retries:
                    await asyncio.sleep(min(2 ** attempt, 8)); continue
                if response.is_error:
                    try: details = response.json()
                    except ValueError: details = response.text
                    raise PolarionError(response.status_code, str(details), details)
                return response.json() if response.content else None
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= self.settings.max_retries: raise
                await asyncio.sleep(min(2 ** attempt, 8))

    async def get(self, path: str, **kwargs: Any) -> Any: return await self.request("GET", path, **kwargs)

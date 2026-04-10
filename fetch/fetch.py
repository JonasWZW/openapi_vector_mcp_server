# -*- coding: utf-8 -*-
"""Fetch module - download OpenAPI JSON from remote URLs."""

import asyncio
import json
import httpx
from pathlib import Path
from dataclasses import dataclass

from config import get_fetch_apps, FETCH_DATAS_DIR, MILVUS_COLLECTION


@dataclass
class AppFetchConfig:
    """Single app fetch configuration."""
    app_name: str
    collection_name: str
    description: str
    url: str

    @property
    def output_filename(self) -> str:
        """Output filename pattern: {app_name}接口文档.json"""
        return f"{self.app_name}接口文档.json"


async def fetch_app(config: AppFetchConfig) -> tuple[str, Path | None]:
    """Fetch OpenAPI JSON for a single app."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(config.url)
            response.raise_for_status()
            data = response.json()

        output_path = FETCH_DATAS_DIR / config.output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return config.app_name, output_path
    except Exception as e:
        return config.app_name, None


async def fetch_all() -> list[Path]:
    """Fetch all apps configured in fetch.yaml."""
    app_configs = get_fetch_apps()
    if not app_configs:
        print("No apps configured in fetch.yaml")
        return []

    configs = [AppFetchConfig(
        app_name=a["app_name"],
        collection_name=a.get("collection_name") or MILVUS_COLLECTION,
        description=a.get("description", ""),
        url=a["url"]
    ) for a in app_configs]
    tasks = [fetch_app(c) for c in configs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    downloaded = []
    for config, result in zip(configs, results):
        if isinstance(result, Exception):
            print(f"Failed to fetch {config.app_name}: {result}")
        elif result[1] is None:
            print(f"Failed to fetch {config.app_name}")
        else:
            print(f"Downloaded: {result[1]}")
            downloaded.append(result[1])

    return downloaded


if __name__ == "__main__":
    asyncio.run(fetch_all())

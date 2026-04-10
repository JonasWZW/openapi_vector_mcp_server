# -*- coding: utf-8 -*-
"""Pipeline - orchestrate fetch -> wash -> vectorize."""

import argparse
import asyncio
import time
import json

from config import FETCH_DATAS_DIR
from fetch.fetch import fetch_all
from wash.wash_to_json import wash_all, get_app_info_map
from vector.vectorize import vectorize_all


STAGE_SEPARATOR = "=" * 60


def print_header(title: str) -> None:
    """Print section header."""
    print(f"\n{STAGE_SEPARATOR}")
    print(f"  {title}")
    print(STAGE_SEPARATOR)


def print_step(title: str) -> None:
    """Print step title within a section."""
    print(f"\n[>>] {title}")


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"  [OK] {msg}")


def print_error(msg: str) -> None:
    """Print error message."""
    print(f"  [FAIL] {msg}")


def print_info(msg: str) -> None:
    """Print info message."""
    print(f"  [INFO] {msg}")


def run_fetch() -> list:
    """Run fetch stage."""
    print_header("Stage 1: Fetch OpenAPI JSON")

    print_step("Fetching from URLs defined in fetch.yaml...")
    start = time.time()
    paths = asyncio.run(fetch_all())
    elapsed = time.time() - start

    if not paths:
        print_error("No files fetched")
        return []
    print_success(f"Fetched {len(paths)} file(s) in {elapsed:.2f}s")
    return paths


def run_wash() -> list:
    """Run wash stage."""
    print_header("Stage 2: Wash OpenAPI JSON")

    print_step("Washing JSON from fetch/datas...")
    start = time.time()
    paths = wash_all()
    elapsed = time.time() - start

    if not paths:
        print_error("No files washed")
        return []
    print_success(f"Washed {len(paths)} app(s) in {elapsed:.2f}s")

    # Print washed apps with API counts
    app_map = get_app_info_map()
    print("\n  Washed apps:")
    for p in paths:
        app_name = p.stem
        info = app_map.get(app_name, {})
        coll = info.get("collection_name", "")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            api_count = data.get("total_apis", 0)
        except Exception:
            api_count = "?"
        print(f"    - {app_name} ({coll}): {api_count} APIs")

    return paths


def run_vectorize() -> None:
    """Run vectorize stage."""
    print_header("Stage 3: Vectorize to Milvus")

    print_step("Creating collections and upserting vectors...")
    start = time.time()
    total = vectorize_all()
    elapsed = time.time() - start

    if total == 0:
        print_error("No operations vectorized")
        return
    print_success(f"Vectorized {total} operation(s) in {elapsed:.2f}s")


def run_pipeline(stage: str = "all") -> None:
    """
    Run the full pipeline: fetch -> wash -> vectorize.

    Args:
        stage: Which stage(s) to run - 'fetch', 'wash', 'vector', or 'all'
    """
    print_header("OpenAPI Vector Pipeline")
    print_info(f"Stages: {stage}")

    total_start = time.time()

    if stage in ("fetch", "all"):
        run_fetch()
        if stage == "fetch":
            print_total_time(total_start)
            return

    if stage in ("wash", "all"):
        run_wash()
        if stage == "wash":
            print_total_time(total_start)
            return

    if stage in ("vector", "all"):
        run_vectorize()

    print_total_time(total_start)


def print_total_time(elapsed: float) -> None:
    """Print total execution time."""
    print(f"\n{STAGE_SEPARATOR}")
    print(f"  Total time: {elapsed:.2f}s")
    print(STAGE_SEPARATOR)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OpenAPI Vector Pipeline - Fetch, Wash, and Vectorize OpenAPI JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py                    Run full pipeline (fetch -> wash -> vector)
  python pipeline.py --stage fetch      Fetch only
  python pipeline.py --stage wash       Wash only
  python pipeline.py --stage vector     Vectorize only
        """
    )
    parser.add_argument(
        "--stage",
        choices=["fetch", "wash", "vector", "all"],
        default="all",
        help="Which stage to run (default: all)",
    )
    args = parser.parse_args()

    run_pipeline(stage=args.stage)

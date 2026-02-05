#!/usr/bin/env python3
"""
Simple web crawler using FlareSolverr.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

FLARESOLVERR_URL = os.getenv("FLARESOLVERR_API_URL", "http://localhost:8191/v1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def crawl(url: str, timeout: int = 60000) -> dict:
    """Fetch a URL using FlareSolverr."""
    start = time.time()
    logging.info(f"Crawling: {url}")

    response = requests.post(
        FLARESOLVERR_URL,
        json={
            "cmd": "request.get",
            "url": url,
            "maxTimeout": timeout,
        },
        timeout=timeout // 1000 + 10,
    )

    elapsed = time.time() - start

    if response.status_code != 200:
        return {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "error": f"FlareSolverr returned {response.status_code}: {response.text}",
            "elapsed": elapsed,
        }

    data = response.json()

    if data.get("status") != "ok":
        return {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "error": data.get("message", "Unknown error"),
            "elapsed": elapsed,
        }

    solution = data.get("solution", {})
    content = solution.get("response")

    if not content or len(content.strip()) < 100:
        return {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "error": "Empty or too short response",
            "elapsed": elapsed,
        }

    logging.info(f"Success in {elapsed:.2f}s")

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "content": content,
        "status_code": solution.get("status"),
        "elapsed": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="Simple FlareSolverr crawler")
    parser.add_argument("url", help="URL to crawl")
    parser.add_argument("-o", "--output", help="Save result to JSON file")
    args = parser.parse_args()

    result = crawl(args.url)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResults saved to: {output_path.absolute()}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

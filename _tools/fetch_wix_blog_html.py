#!/usr/bin/env python3
"""Download a numbered range of public Wix Blog pages from its sitemap."""

from __future__ import annotations

import argparse
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit


SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def encoded_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe="/%:@-._~"), parts.query, parts.fragment))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sitemap", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start", type=int, required=True, help="1-based first item in last-modified order")
    parser.add_argument("--end", type=int, required=True, help="1-based final item, inclusive")
    args = parser.parse_args()

    root = ET.parse(args.sitemap).getroot()
    items = sorted(
        [
            (node.find("s:lastmod", SITEMAP_NS).text, node.find("s:loc", SITEMAP_NS).text)
            for node in root.findall("s:url", SITEMAP_NS)
        ],
        reverse=True,
    )
    if args.start < 1 or args.end < args.start or args.end > len(items):
        parser.error(f"range must be within 1..{len(items)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index in range(args.start, args.end + 1):
        _, url = items[index - 1]
        target = args.output_dir / f"{index:03}.html"
        if target.exists() and target.stat().st_size:
            print(f"{index:03}/{args.end:03} already downloaded", flush=True)
            continue
        request = urllib.request.Request(
            encoded_url(url),
            headers={"User-Agent": "Mozilla/5.0 LisaRecMigration/1.0"},
        )
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    target.write_bytes(response.read())
                last_error = None
                break
            except Exception as error:  # network errors vary by platform
                last_error = error
                if attempt < 3:
                    time.sleep(attempt * 1.5)
        if last_error:
            raise last_error
        print(f"{index:03}/{args.end:03} {target.stat().st_size:>8} bytes {url}", flush=True)
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

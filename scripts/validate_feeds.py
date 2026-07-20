#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_rss import DATA_OUT, FEEDS, decode_payload, encode_payload

TIMEOUT = 12
WORKERS = 16
USER_AGENT = "Mozilla/5.0 (compatible; FeedValidator/1.0)"
X_CATEGORY = "X (Twitter)"
TRUSTED_X_DOMAINS = {"xcancel.com", "nitter.poast.org", "nitter.net"}


def load_feeds() -> dict:
    if FEEDS.exists():
        return json.loads(FEEDS.read_text(encoding="utf-8"))
    if DATA_OUT.exists():
        return json.loads(decode_payload(DATA_OUT.read_text(encoding="utf-8")))
    raise FileNotFoundError("No feeds source found.")


def trusted_x_feed(url: str, category: str) -> bool:
    if category != X_CATEGORY:
        return False
    host = urlparse(url).netloc
    return host in TRUSTED_X_DOMAINS


def check_feed(url: str, category: str = "") -> bool:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return 200 <= response.status < 400
    except urllib.error.HTTPError as error:
        if trusted_x_feed(url, category) and error.code in {403, 429}:
            return True
        return 200 <= error.code < 400
    except Exception:
        return trusted_x_feed(url, category)


def main() -> int:
    try:
        payload = load_feeds()
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 1

    items = payload.get("items", [])
    if not items:
        print("No feed items found.", file=sys.stderr)
        return 1

    results: dict[str, bool] = {}

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_map = {
            executor.submit(check_feed, item.get("u", ""), item.get("c", "")): item.get("u", "")
            for item in items
            if item.get("u")
        }
        for future in as_completed(future_map):
            url = future_map[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = False

    active = 0
    for item in items:
        url = item.get("u", "")
        item["ok"] = bool(results.get(url, False))
        if item["ok"]:
            active += 1

    payload["t"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload["items"] = items

    FEEDS.parent.mkdir(parents=True, exist_ok=True)
    FEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    DATA_OUT.write_text(encode_payload(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")

    build = subprocess.run([sys.executable, str(Path(__file__).with_name("build_rss.py"))], check=False)
    if build.returncode != 0:
        return build.returncode

    print(f"Checked {len(items)} feeds. Active: {active}. Inactive: {len(items) - active}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

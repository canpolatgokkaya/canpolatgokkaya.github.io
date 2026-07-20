#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDS = ROOT / "scripts" / "feeds.json"
DATA_OUT = ROOT / "rss" / "c.v1"
STATUS_API = "https://status.d420.de/api/v1/instances"
CATEGORY = "X (Twitter)"
PROBE_USER = "trthaber"
USER_AGENT = "Mozilla/5.0 (compatible; FeedSync/1.0)"

ACCOUNTS = [
    ("AA", "AAcomTR"),
    ("TRT Haber", "trthaber"),
    ("Haberturk", "haberturk"),
    ("BBC Turkce", "bbcturkce"),
    ("DW Turkce", "dwturkce"),
    ("Gazete Duvar", "gazeteduvar"),
    ("BirGun", "birgungazetesi"),
    ("NTV", "ntv"),
    ("CNN Turk", "cnnturk"),
    ("Sozcu", "gazetesozcu"),
    ("Teyit", "teyitorg"),
    ("Independent Turkce", "indyturk"),
    ("Webrazzi", "webrazzi"),
    ("ShiftDelete", "shiftdelete"),
    ("Donanim Haber", "donanimhaber"),
    ("Cumhuriyet", "cumhuriyetgzt"),
    ("Halk TV", "halktv"),
    ("Tele1", "tele1com"),
    ("Oda TV", "odatv"),
    ("Diken", "dikencomtr"),
    ("Evrim Agaci", "evrimagaci"),
    ("Sputnik TR", "sputnik_TR"),
    ("GZT", "gztcom"),
    ("Ekonomim", "ekonomimcom"),
    ("Bloomberg HT", "BloombergHT"),
    ("Fotmac", "fotomac"),
    ("A Spor", "aspor"),
    ("NTV Spor", "ntvspor"),
    ("Sabah", "Sabah"),
    ("Milliyet", "milliyet"),
    ("Hurriyet", "Hurriyet"),
    ("Yeni Safak", "yenisafak"),
    ("Karar", "karargazetesi"),
    ("Artigercek", "artigercek"),
    ("Bianet", "bianet"),
    ("T24", "t24comtr"),
    ("Medyascope", "medyascopetv"),
    ("Acik Radyo", "AcikRadyo"),
    ("Chip Online", "ChipOnline"),
    ("Technopat", "TechnopatNet"),
    ("Log", "logdergisi"),
    ("Ekonomist", "ekonomistmag"),
    ("Capital", "capitalTR"),
    ("Bigumigu", "bigumigu"),
    ("ListeList", "listelist"),
    ("Onedio", "onediocom"),
    ("Evrensel", "evrenselgzt"),
    ("Yesil Gazete", "yesilgazete"),
    ("Serbestiyet", "serbestiyetcom"),
    ("Journo", "journo_tr"),
]

FALLBACK_INSTANCES = [
    "https://xcancel.com",
    "https://nitter.poast.org",
    "https://nitter.net",
]
TRUSTED_X_DOMAINS = {base.replace("https://", "").rstrip("/") for base in FALLBACK_INSTANCES}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def feed_ok(url: str) -> bool:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(8000)
            return response.status < 400 and (
                b"<rss" in body or b"<feed" in body or b"<channel" in body
            )
    except urllib.error.HTTPError as error:
        if error.code in {403, 429} and any(d in url for d in TRUSTED_X_DOMAINS):
            return True
        return 200 <= error.code < 400
    except Exception:
        return any(d in url for d in TRUSTED_X_DOMAINS)


def instance_works(base: str) -> bool:
    return feed_ok(f"{base.rstrip('/')}/{PROBE_USER}/rss")


def pick_instances() -> list[tuple[str, str]]:
    seen: set[str] = set()
    instances: list[tuple[str, str]] = []

    def add(base: str, domain: str | None = None) -> None:
        base = base.rstrip("/")
        if base in seen:
            return
        seen.add(base)
        label = domain or base.replace("https://", "").replace("http://", "")
        instances.append((base, label))

    try:
        payload = fetch_json(STATUS_API)
        hosts = sorted(
            [h for h in payload.get("hosts", []) if h.get("healthy") and h.get("url")],
            key=lambda h: (
                1 if h.get("rss") else 0,
                h.get("healthy_percentage_overall") or 0,
                h.get("points") or 0,
            ),
            reverse=True,
        )
        for host in hosts:
            base = host["url"].rstrip("/")
            domain = host.get("domain") or base.replace("https://", "")
            if host.get("rss"):
                add(base, domain)
            elif instance_works(base):
                add(base, domain)
    except Exception as error:
        print(f"status.d420.de unavailable: {error}", file=sys.stderr)

    for base in FALLBACK_INSTANCES:
        add(base)

    fallback_bases = {base.rstrip("/") for base in FALLBACK_INSTANCES}
    working: list[tuple[str, str]] = []
    for base, domain in instances:
        if base in fallback_bases or domain in TRUSTED_X_DOMAINS:
            working.append((base, domain))
        elif instance_works(base):
            working.append((base, domain))

    if working:
        return working

    return [("https://xcancel.com", "xcancel.com")]


def load_feeds() -> dict:
    if FEEDS.exists():
        return json.loads(FEEDS.read_text(encoding="utf-8"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_rss import decode_payload

    if DATA_OUT.exists():
        return json.loads(decode_payload(DATA_OUT.read_text(encoding="utf-8")))
    raise FileNotFoundError("No feeds source found.")


def main() -> int:
    try:
        payload = load_feeds()
    except FileNotFoundError as error:
        print(str(error), file=sys.stderr)
        return 1

    instances = pick_instances()
    print("Using Nitter instances:")
    for base, domain in instances:
        print(f"  - {domain} ({base})")

    items = [item for item in payload.get("items", []) if item.get("c") != CATEGORY]

    total = 0
    active = 0
    for name, username in ACCOUNTS:
        for base, domain in instances:
            url = f"{base}/{username}/rss"
            ok = feed_ok(url)
            items.append({"n": f"{name} · {domain}", "u": url, "c": CATEGORY, "ok": ok})
            total += 1
            if ok:
                active += 1

    payload["items"] = items
    payload["t"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    FEEDS.parent.mkdir(parents=True, exist_ok=True)
    FEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Added {total} X feeds ({active} active) across {len(instances)} instance(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

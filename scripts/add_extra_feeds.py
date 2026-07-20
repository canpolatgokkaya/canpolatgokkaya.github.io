#!/usr/bin/env python3
"""Add Podcast, Oyun, and Resmi Kurum feeds."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDS = ROOT / "scripts" / "feeds.json"

NEW_FEEDS = [
    # Podcast
    ("Socrates", "https://socratesdergi.com/feed/", "Podcast"),
    ("Geri Dönüyoruz", "https://feeds.transistor.fm/geri-donuyoruz", "Podcast"),
    ("Ruşen Çakır", "https://feeds.megaphone.fm/rusen-cakir", "Podcast"),
    ("Bant Mag Podcast", "https://www.bantmag.com/feed/podcast/", "Podcast"),
    ("Bir Aile Meselesi", "https://media.rss.com/biailemeselesi/feed.xml", "Podcast"),
    ("Kendine İyi Davran", "https://www.spreaker.com/show/4905636/episodes/feed", "Podcast"),
    ("BBC Türkçe", "https://feeds.bbci.co.uk/turkce/rss.xml", "Podcast"),
    ("6 Minute English", "https://feeds.bbci.co.uk/learningenglish/english/features/6-minute-english/rss", "Podcast"),
    ("Global News BBC", "https://feeds.bbci.co.uk/news/world/rss.xml", "Podcast"),
    ("Journo", "https://journo.com.tr/feed/", "Podcast"),
    ("Medyascope", "https://medyascope.tv/feed/", "Podcast"),
    ("Gazete Duvar", "https://www.gazeteduvar.com.tr/feed/", "Podcast"),
    ("ListeList", "https://listelist.com/feed/", "Podcast"),
    # Oyun
    ("Mobidictum", "https://mobidictum.com/feed/", "Oyun"),
    ("Turuncu Levye", "https://www.turunculevye.com/feed/", "Oyun"),
    ("Turkmmo", "https://www.turkmmo.com/feed/", "Oyun"),
    ("IGN Türkiye", "https://tr.ign.com/feed.xml", "Oyun"),
    ("Steam Haberler", "https://store.steampowered.com/feeds/news/", "Oyun"),
    ("PC Gamer", "https://www.pcgamer.com/rss/", "Oyun"),
    ("Merlin'in Kazanı", "https://www.merlininkazani.com/rss/", "Oyun"),
    ("Donanım Haber Oyun", "https://www.donanimhaber.com/rss/tum/oyun", "Oyun"),
    ("ShiftDelete Oyun", "https://shiftdelete.net/oyun/feed", "Oyun"),
    ("Webrazzi Oyun", "https://webrazzi.com/kategori/oyun/feed", "Oyun"),
    # Resmi Kurum
    ("Enerji Bakanlığı Haber", "https://enerji.gov.tr/rss/haberler.xml", "Resmi Kurum"),
    ("Enerji Bakanlığı Duyuru", "https://enerji.gov.tr/rss/duyurular.xml", "Resmi Kurum"),
    ("Çevre Şehircilik", "https://www.csb.gov.tr/rss", "Resmi Kurum"),
    ("AA Güncel", "https://www.aa.com.tr/tr/rss/default?cat=guncel", "Resmi Kurum"),
    ("AA Ekonomi", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi", "Resmi Kurum"),
    ("AA Spor", "https://www.aa.com.tr/tr/rss/default?cat=spor", "Resmi Kurum"),
    ("AA Bilim Teknoloji", "https://www.aa.com.tr/tr/rss/default?cat=bilim-teknoloji", "Resmi Kurum"),
    ("AA Sağlık", "https://www.aa.com.tr/tr/rss/default?cat=saglik", "Resmi Kurum"),
    ("AA Dünya", "https://www.aa.com.tr/tr/rss/default?cat=dunya", "Resmi Kurum"),
    ("TSE", "https://www.tse.org.tr/rss", "Resmi Kurum"),
    ("TİKA", "https://www.tika.gov.tr/rss", "Resmi Kurum"),
]


def main() -> int:
    if not FEEDS.exists():
        print(f"Missing {FEEDS}", file=sys.stderr)
        return 1

    payload = json.loads(FEEDS.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    existing_urls = {item.get("u", "").rstrip("/") for item in items}

    added = 0
    skipped = 0
    for name, url, category in NEW_FEEDS:
        key = url.rstrip("/")
        if key in existing_urls:
            skipped += 1
            continue
        items.append({"n": name, "u": url, "c": category, "ok": True})
        existing_urls.add(key)
        added += 1

    payload["items"] = items
    payload["t"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    FEEDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Added {added} feeds, skipped {skipped} duplicates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

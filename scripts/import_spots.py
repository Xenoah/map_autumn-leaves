#!/usr/bin/env python3
"""One-time, reproducible import of Wikipedia/Wikidata geolocated sightseeing candidates.

Candidates are NOT observed autumn foliage reports. They are labelled accordingly.
Source: rtcode337/travel-log-data tourist/spots.csv (Wikipedia CC BY-SA 4.0,
Wikidata CC0). Requires attribution as documented in data/ATTRIBUTION.md.
Run again after deleting data/catalog-import.done, or pass --force.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/spots.json"
MARKER = ROOT / "data/catalog-import.done"
URL = "https://raw.githubusercontent.com/rtcode337/travel-log-data/main/tourist/spots.csv"
RANK = {r: i for i, r in enumerate("ABCDE")}
# Diversity limits avoid turning a foliage map into an arbitrary 10k-place POI dump.
QUOTA = {"自然": 12, "山": 9, "公園": 8, "寺院": 4,
         "神社": 3, "城跡・史跡": 3, "温泉": 2}
NATURE = re.compile(r"峡|渓|谷|滝|瀑|湖|沼|池|森林|自然公園|国立公園|高原|湿原|原生林|草原|森|樹|ブナ|川|沢|洞|峡谷|紅葉")
NOT_NATURE = re.compile(r"海峡|海岸|海水浴|浜|ビーチ|岬|離島|島嶼|鍾乳洞|石灰洞|砂丘|珊瑚|サンゴ")
NOT_PARK = re.compile(r"ひまわり|チューリップ|ローズ|フラワー|サッカー|スタジアム|球場|運動公園|総合運動|水族館|動物園|サファリ|プール|ゴルフ|遊園地|海浜|海水浴|ビーチ|水上公園|自転車競技場")
AUTUMN = re.compile(r"紅葉|もみじ|モミジ|楓|カエデ|イチョウ|銀杏|黄葉")
FORCE = {"十和田湖", "八方尾根", "白馬八方尾根", "清水寺", "東福寺", "永観堂", "瑠璃光院"}
CAMERAS = [
    ("青森", re.compile(r"^十和田湖$"),
     "https://www.city.towada.lg.jp/kanko/spot/livecamera.html", "十和田市公式・十和田湖休屋カメラ"),
    ("長野", re.compile(r"八方尾根"),
     "https://www.happo-one.jp/trekking/livecamera/", "白馬八方尾根公式ライブカメラ"),
]
DESCRIPTIONS = {
    "自然": "自然景勝地の観賞候補。現在の紅葉状況は未確認です。",
    "山": "山岳・高原の観賞候補。色づきは標高で異なり、現在の観測情報は未確認です。",
    "公園": "公園・庭園の観賞候補。現地の紅葉状況は未確認です。",
    "寺院": "寺院周辺の観賞候補。現地の紅葉状況は未確認です。",
    "神社": "神社周辺の観賞候補。現地の紅葉状況は未確認です。",
    "城跡・史跡": "史跡・城跡周辺の観賞候補。現地の紅葉状況は未確認です。",
    "温泉": "温泉地周辺の観賞候補。現地の紅葉状況は未確認です。",
}


def normalize(name: str) -> str:
    text = unicodedata.normalize("NFKC", name).lower()
    text = re.sub(r"\s|[・「」『』()（）、.,/]", "", text)
    return text.replace("ノ", "").replace("の", "").replace("ヶ", "ケ")


def prefecture(name: str) -> str:
    return name if name == "北海道" else name.rstrip("都府県")


def suitable(row: dict) -> bool:
    series, name, rank = row.get("series", ""), row.get("name", ""), row.get("rank", "")
    if not name or series not in QUOTA or rank not in RANK:
        return False
    strong = bool(AUTUMN.search(name)) or name in FORCE
    if series == "自然":
        return not NOT_NATURE.search(name) and bool(NATURE.search(name)) and (RANK[rank] <= 2 or strong)
    if series == "山":
        return RANK[rank] <= 2 or strong
    if series == "公園":
        return not NOT_PARK.search(name) and (RANK[rank] <= 2 or strong)
    if series in ("寺院", "神社", "城跡・史跡", "温泉"):
        if series == "城跡・史跡" and not re.search(r"城|城址|城跡|城山|公園|庭園", name):
            return False
        return RANK[rank] <= 1 or strong
    return False


def article_url(row: dict) -> str:
    # The upstream CSV description includes the original page title. We do not
    # reproduce the upstream prose, but retain a per-place provenance link.
    match = re.search(r"\[ja\.wikipedia:([^\]]+)\]", row.get("description", ""))
    title = match.group(1) if match else row["name"]
    return "https://ja.wikipedia.org/wiki/" + quote(title.replace(" ", "_"), safe="/()")


def already_present(candidate: dict, known: list[dict]) -> bool:
    name, pref = normalize(candidate["name"]), candidate["prefecture"]
    for existing in known:
        if existing["prefecture"] != pref:
            continue
        other = normalize(existing["name"])
        dlat = abs(existing["lat"] - candidate["lat"])
        dlon = abs(existing["lon"] - candidate["lon"])
        if name == other:
            return True
        # Only merge very-near positions when names clearly overlap.
        if dlat < .012 and dlon < .012 and min(len(name), len(other)) >= 4:
            if name in other or other in name:
                return True
    return False


def source_row_to_spot(row: dict) -> dict | None:
    name, pref = row["name"].strip(), prefecture(row["region"].strip())
    try:
        lat, lon = float(row["lat"]), float(row["lng"])
    except (ValueError, KeyError, TypeError):
        return None
    if not 24.0 < lat < 46.5 or not 122.0 < lon < 154.6:
        return None
    key = hashlib.sha1(f"{pref}:{row['key'] or name}".encode()).hexdigest()[:14]
    series = row["series"]
    spot = {
        "id": "wiki-" + key,
        "name": name,
        "prefecture": pref,
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "typicalSeason": "地域・標高による（未確認）",
        "description": DESCRIPTIONS[series],
        "candidate": True,
        "category": series,
        "sourceName": "Wikipedia / Wikidata（観光地位置情報）",
        "sourceUrl": article_url(row)
    }
    for camera_pref, pattern, url, title in CAMERAS:
        if pref == camera_pref and pattern.search(name):
            spot["camera"] = {"url": url, "title": title, "mode": "directory"}
            break
    return spot


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--force", action="store_true", help="regenerate selections; preserves existing IDs")
    ns = args.parse_args()
    if MARKER.exists() and not ns.force:
        print("Wikipedia candidate import already completed; no network request.")
        return 0
    existing = json.loads(CATALOG.read_text("utf-8"))
    if not isinstance(existing, list):
        raise ValueError("data/spots.json must be an array")
    known_pref = {s["prefecture"] for s in existing}
    req = Request(URL, headers={"User-Agent":
        "KOYO-LIVE-attribution-import/1.2 (+https://github.com/Xenoah/map_autumn-leaves)"})
    try:
        with urlopen(req, timeout=45) as response:
            source_text = response.read(6 * 1024 * 1024).decode("utf-8-sig")
    except Exception as exc:
        # A third-party outage must not take GitHub Pages offline.
        print(f"::warning::Open coordinate source unavailable: {exc}")
        return 0
    reader = csv.DictReader(io.StringIO(source_text))
    if not set(("name", "region", "series", "rank", "key", "lat", "lng")).issubset(reader.fieldnames or []):
        print("::warning::Unexpected third-party CSV schema; leaving catalog intact")
        return 0
    grouped = defaultdict(lambda: defaultdict(list))
    for row in reader:
        pref = prefecture(row["region"])
        if pref not in known_pref or not suitable(row):
            continue
        spot = source_row_to_spot(row)
        if spot:
            priority = (0 if AUTUMN.search(spot["name"]) or spot["name"] in FORCE else 1,
                        RANK[row["rank"]], spot["name"])
            grouped[pref][row["series"]].append((priority, spot))
    additions = []
    pool = list(existing)
    for pref in sorted(known_pref):
        for series, quota in QUOTA.items():
            candidates = sorted(grouped[pref][series], key=lambda item: item[0])
            count = 0
            for _, spot in candidates:
                if count >= quota:
                    break
                if already_present(spot, pool):
                    continue
                pool.append(spot)
                additions.append(spot)
                count += 1
    if not additions:
        print("::warning::No additional spots matched the reliable geodata filters")
        return 0
    data = existing + additions
    ids = [spot["id"] for spot in data]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate catalog IDs after import")
    # Preserve the original curated ordering; group imported candidates by prefecture.
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "source": URL,
        "sourceLicense": "CC BY-SA 4.0 and Wikidata CC0 (see data/ATTRIBUTION.md)",
        "importedAtUTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "added": len(additions),
        "total": len(data),
        "candidatesByPrefecture": dict(sorted(Counter(s["prefecture"] for s in additions).items()))
    }
    MARKER.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Nationwide catalog expansion:", json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

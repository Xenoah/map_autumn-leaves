"""Build tiny on-demand map catalogues and an offline-friendly HTML fallback."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPACT_SCHEMA = 1
# Compact row indices: id, name, prefecture, lat, lon, camera_url,
# camera_mode, candidate_bit, elevation.
FIELDS = ("id", "name", "prefecture", "lat", "lon",
          "camera_url", "camera_mode", "candidate", "elevation")
FALLBACK_LIMIT = 58


def minijson(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def compact_catalog(spots: list[dict]) -> dict:
    rows = []
    for spot in spots:
        camera = spot.get("camera") or {}
        rows.append([
            spot["id"], spot["name"], spot["prefecture"],
            round(float(spot["lat"]), 6), round(float(spot["lon"]), 6),
            camera.get("url", ""), camera.get("mode", ""),
            int(bool(spot.get("candidate"))), spot.get("elevation") or 0
        ])
    return {"schemaVersion": COMPACT_SCHEMA, "fields": FIELDS, "rows": rows}


def offline_fallback(spots: list[dict], live: dict) -> list[dict]:
    # Keep cameras and reported foliage locally available even without JSON fetch.
    # Avoid embedding descriptions/attributions for all 1,083 locations in HTML.
    curated = [spot for spot in spots if not spot.get("candidate")]
    ordered = ([spot for spot in spots if spot.get("camera")] +
               [spot for spot in curated if spot["id"] in live.get("reports", {})] +
               curated)
    selected = []
    seen = set()
    for spot in ordered:
        if spot["id"] in seen:
            continue
        selected.append(spot)
        seen.add(spot["id"])
        if len(selected) >= FALLBACK_LIMIT:
            break
    return selected


def build_outputs(root: Path = ROOT) -> dict:
    data_dir = root / "data"
    spots = json.loads((data_dir / "spots.json").read_text(encoding="utf-8"))
    live = json.loads((data_dir / "live.json").read_text(encoding="utf-8"))
    index = compact_catalog(spots)
    compact_text = minijson(index)
    (data_dir / "spots-lite.json").write_text(compact_text + "\n", encoding="utf-8")

    details = defaultdict(list)
    for spot in spots:
        details[spot["prefecture"]].append(spot)
    detail_dir = data_dir / "prefectures"
    detail_dir.mkdir(parents=True, exist_ok=True)
    for pref, items in details.items():
        (detail_dir / f"{pref}.json").write_text(
            minijson(items) + "\n", encoding="utf-8"
        )
    # The generated subfolder owns .json files. Do not keep removed provinces around.
    for path in detail_dir.glob("*.json"):
        if path.stem not in details:
            path.unlink()

    fallback = offline_fallback(spots, live)
    boundaries = [[min(s["lat"] for s in spots), min(s["lon"] for s in spots)],
                  [max(s["lat"] for s in spots), max(s["lon"] for s in spots)]]
    embedded = minijson({"spots": fallback, "live": live, "bounds": boundaries})
    # Keep script-breaking tags out of inline JSON.
    embedded = embedded.replace("<", r"\u003c").replace(">", r"\u003e").replace("&", r"\u0026")
    template = (root / "scripts/index.template.html").read_text(encoding="utf-8")
    if "__EMBEDDED_DATA__" not in template:
        raise ValueError("Missing __EMBEDDED_DATA__ placeholder")
    html = template.replace("__EMBEDDED_DATA__", embedded)
    (root / "index.html").write_text(html, encoding="utf-8")
    metrics = {
        "spots": len(spots),
        "cameras": sum(bool(s.get("camera")) for s in spots),
        "details_files": len(details),
        "fallback_spots": len(fallback),
        "html_bytes": len(html.encode("utf-8")),
        "compact_bytes": len(compact_text.encode("utf-8")),
        "source_bytes": (data_dir / "spots.json").stat().st_size
    }
    return metrics


if __name__ == "__main__":
    print("Built lightweight map assets:", json.dumps(build_outputs(), ensure_ascii=False))

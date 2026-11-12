#!/usr/bin/env python3
"""Write simplified polity outlines from Historical Basemaps.

Source: https://github.com/aourednik/historical-basemaps (GPL-3.0).
The output of this script is the public library. Coordinates are not copied
into the LearnWhale repository.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "geojson"
SOURCE = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson"
YEAR_FILES = {
    -500: "world_bc500.geojson",
    1279: "world_1279.geojson",
    1783: "world_1783.geojson",
}

MONGOL_IDS = {
    "Great Khanate": "great-khanate-1279",
    "Khanate of the Golden Horde": "golden-horde-1279",
    "Ilkhanate": "ilkhanate-1279",
    "Chagatai Khanate": "chagatai-1279",
    "Ryazan": "ryazan-1279",
    "Tibet": "tibet-1279",
    "Novgorod": "novgorod-1279",
    "Seljuk Caliphate": "seljuk-1279",
}


def download(name: str) -> dict:
    cache = Path("/tmp/historical-basemaps") / name
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists() or cache.stat().st_size == 0:
        print(f"download {name}")
        urllib.request.urlretrieve(f"{SOURCE}/{name}", cache)
    return json.loads(cache.read_text())


def perpendicular(point, start, end) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    qx, qy = ax + t * dx, ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def rdp(points: list[list[float]], epsilon: float) -> list[list[float]]:
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    index, distance = 0, 0.0
    for cursor, point in enumerate(points[1:-1], start=1):
        span = perpendicular(point, start, end)
        if span > distance:
            index, distance = cursor, span
    if distance <= epsilon:
        return [start, end]
    return rdp(points[: index + 1], epsilon)[:-1] + rdp(points[index:], epsilon)


def outers(geometry: dict) -> list[list[list[float]]]:
    kind = geometry["type"]
    coords = geometry["coordinates"]
    if kind == "Polygon":
        polygons = [coords]
    elif kind == "MultiPolygon":
        polygons = coords
    else:
        raise SystemExit(f"unsupported geometry {kind}")
    rings: list[list[list[float]]] = []
    for polygon in polygons:
        outer = [[round(point[0], 5), round(point[1], 5)] for point in polygon[0]]
        if len(outer) > 250:
            outer = [[round(point[0], 5), round(point[1], 5)] for point in rdp(outer, 0.04)]
        if len(outer) >= 4:
            if outer[0] != outer[-1]:
                outer.append(outer[0])
            rings.append(outer)
    return rings


def write_feature(feature_id: str, name: str, year: int, precision: int, rings: list[list[list[float]]]) -> None:
    if not rings:
        raise SystemExit(f"{feature_id} has no rings")
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": feature_id,
                    "name": name,
                    "year": year,
                    "borderPrecision": precision,
                    "source": "https://github.com/aourednik/historical-basemaps",
                    "license": "GPL-3.0",
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[ring] for ring in rings],
                },
            }
        ],
    }
    path = OUT / f"{feature_id}.geojson"
    path.write_text(json.dumps(payload))
    print(f"wrote {path.name} rings={len(rings)} points={sum(len(ring) for ring in rings)}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    persia = download(YEAR_FILES[-500])
    persia_features = [feature for feature in persia["features"] if feature["properties"].get("NAME") == "Achaemenid Empire"]
    if len(persia_features) != 1:
        raise SystemExit(f"expected one Achaemenid Empire, found {len(persia_features)}")
    feature = persia_features[0]
    write_feature(
        "achaemenid-500",
        "Achaemenid Empire",
        -500,
        int(feature["properties"]["BORDERPRECISION"]),
        outers(feature["geometry"]),
    )

    mongol = download(YEAR_FILES[1279])
    found: set[str] = set()
    for feature in mongol["features"]:
        name = feature["properties"].get("NAME")
        if feature["properties"].get("SUBJECTO") != "Mongol Empire":
            continue
        feature_id = MONGOL_IDS.get(name or "")
        if feature_id is None:
            raise SystemExit(f"unexpected Mongol subject {name!r}")
        found.add(name or "")
        write_feature(
            feature_id,
            name or "",
            1279,
            int(feature["properties"]["BORDERPRECISION"]),
            outers(feature["geometry"]),
        )
    missing = set(MONGOL_IDS) - found
    if missing:
        raise SystemExit(f"missing Mongol subjects: {sorted(missing)}")

    america = download(YEAR_FILES[1783])
    states = [feature for feature in america["features"] if feature["properties"].get("NAME") == "United States of America"]
    if len(states) != 1:
        raise SystemExit(f"expected one United States of America in 1783, found {len(states)}")
    feature = states[0]
    write_feature(
        "united-states-1783",
        "United States",
        1783,
        int(feature["properties"]["BORDERPRECISION"]),
        outers(feature["geometry"]),
    )


if __name__ == "__main__":
    main()

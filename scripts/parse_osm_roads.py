"""Parses the cached Overpass raw response into a clean roads GeoJSON.

Data source: OpenStreetMap via the public Overpass API, fetched once for
the Dirai/Sunamganj AOI (91.15, 24.5, 91.5, 24.8) and cached at
data/cache/osm_roads_raw_response.json -- rerunning this script does not
hit Overpass again. (c) OpenStreetMap contributors, ODbL.

Run: python3 scripts/parse_osm_roads.py
Output: data/raw/roads_sunamganj.geojson
"""

import json

import geopandas as gpd
from shapely.geometry import LineString

CACHE_PATH = "data/cache/osm_roads_raw_response.json"
OUT_PATH = "data/raw/roads_sunamganj.geojson"


def main():
    with open(CACHE_PATH) as f:
        elements = json.load(f)["elements"]

    rows = []
    for el in elements:
        tags = el.get("tags", {})
        highway = tags.get("highway")
        if not highway:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el.get("geometry", []) if pt]
        if len(coords) < 2:
            continue
        rows.append({
            "osm_id": el["id"],
            "highway": highway,
            "name": tags.get("name", ""),
            "surface": tags.get("surface", ""),
            "geometry": LineString(coords),
        })

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    gdf.to_file(OUT_PATH, driver="GeoJSON")
    print(f"wrote {len(gdf)} road segments to {OUT_PATH}")
    print(gdf["highway"].value_counts())


if __name__ == "__main__":
    main()

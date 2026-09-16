# Data

Every input is real, public data. Nothing here is synthetic. Two real
naming/boundary surprises are documented below rather than smoothed over —
finding them is part of what this phase was for.

## Sources

| File | Source | Real numbers |
|---|---|---|
| `flood_extent_sunamganj_2026-07-13.geojson` | Regenerated from `geohealth-risk-mapping`'s Phase H5 method (`scripts/generate_flood_extent.py`): real Sentinel-1 RTC via Microsoft Planetary Computer, before (2026-06-19) vs. during (2026-07-13), Otsu-threshold change detection | 8.0% of AOI newly flooded, 418 polygons after SAR-speckle cleanup — exact match to H5's documented result, including identical Sentinel-1 scene IDs |
| `health_facilities_sunamganj.geojson` | OpenStreetMap, copied from `geohealth-risk-mapping`'s already-fetched extract | 13 real facilities |
| `worldpop_2020_sunamganj_aoi.tif` | WorldPop 2020 building-constrained population, clipped from `geohealth-risk-mapping`'s country-wide raster to this AOI (14MB → 97KB) | 717,209 people — matches H5's documented AOI total |
| `roads_sunamganj.geojson` | OpenStreetMap via the public Overpass API, fetched once and cached at `data/cache/osm_roads_raw_response.json` (not re-fetched on rerun) | 3,398 real road segments |
| `upazila_boundaries_sunamganj_aoi.geojson` | HDX "Bangladesh - Subnational Administrative Boundaries" (`cod-ab-bgd`), BBS/ITOS via UNOCHA ROAP, filtered to upazilas intersecting the AOI | 8 upazilas |
| `*_utm46n.geojson` | The four vector layers above, reprojected to EPSG:32646 (UTM zone 46N) for accurate metric distance/area analysis | — |

AOI: `(91.15, 24.5, 91.5, 24.8)` — the exact bounding box `geohealth-risk-mapping`'s
Phase H5 used for Dirai, Sunamganj.

## Two real surprises, documented rather than hidden

1. **The AOI spans 4 districts, not 1.** A rectangular satellite-processing
   bounding box doesn't respect administrative boundaries. The 8
   intersecting upazilas span **Sunamganj** (Derai, Jagannathpur, Shalla),
   **Habiganj** (Ajmiriganj, Baniachong, Nabiganj), **Netrakona**
   (Khaliajuri), and **Kishoreganj** (Itna). Any per-upazila analysis in
   later phases covers all 8, not just Sunamganj district's own three.
2. **A real name mismatch, same lesson as `humanitarian-im-toolkit`'s
   Phase R3.** `geohealth-risk-mapping`'s own documentation spells the
   flood-affected upazila "**Dirai**." HDX's official COD-AB record spells
   it "**Derai**." No code here joins on that name — everything keys on
   the official `adm3_pcode` — but it's worth naming out loud as the same
   failure mode P-code joins exist to prevent.

## Regenerating

```
# Requires geohealth-risk-mapping checked out as a sibling directory
# (../geohealth-risk-mapping) -- see scripts/generate_flood_extent.py's
# own docstring.
../geohealth-risk-mapping/.venv/bin/python3 scripts/generate_flood_extent.py
python3 scripts/parse_osm_roads.py
```

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

## `processed/` — Phase Q1 outputs (real QGIS GUI work, not scripted)

| File | Produced by | Real numbers |
|---|---|---|
| `health_facility_buffers_2km.gpkg` | QGIS Processing → Buffer, 2000m, on `health_facilities_utm46n` | 13 buffer polygons |
| `health_facilities_with_upazila.gpkg` | QGIS Processing → Join attributes by location (`within`), facilities × upazila boundaries | 13/13 facilities matched |
| `flooded_roads.gpkg` | QGIS Processing → Extract by location (`intersect`), roads × the dissolved flood extent | 283 of 3,398 road segments (8.3%) — consistent with the 8.0% of the AOI that was flooded |

**A real export bug, caught and fixed:** all three files came out of QGIS's
"Save Features As" with no CRS attached at all (confirmed with `ogrinfo`,
not just a display glitch). The coordinate values themselves were still
correct UTM 46N meters (`total_bounds` matched the AOI exactly) — only the
CRS label was missing on export — so the fix was assigning EPSG:32646
back onto each file, not reprojecting anything.

**Topology check on `roads_utm46n`** ("must not have dangles" rule, QGIS's
Topology Checker plugin): **5,023 dangling endpoints** found, out of a
theoretical max of 6,796 (3,398 segments × 2 ends). Expected for raw rural
OSM data, not an error: real dead-end tracks/driveways, artifacts of the
rectangular AOI cutting roads at its edge, and incomplete rural mapping
connectivity. Not fixed wholesale — Q2's network analysis will need to
account for this rather than assume a fully connected graph.

## Phase Q2 outputs — network accessibility

| File | Produced by | Real numbers |
|---|---|---|
| `service_area_full_network.gpkg` | QGIS Network Analysis → Service area (from layer), `roads_utm46n`, 13 facilities, 5000m shortest-distance cost | 13 features (one per facility) |
| `service_area_full_network.geojson` | This repo's `scripts/compute_service_areas.py` (networkx), same network/facilities/cost, as a cross-check | 537,407 m unique reachable length |
| `service_area_degraded_network.geojson` | Same script, on `roads_flood_degraded` | 438,985 m unique reachable length |
| `q2_accessibility_summary.csv` | Same script | see below |

**Real result:** reachable network length drops **18.3%** when the 283
flood-affected road segments are removed — 2,447 segments lose access
entirely, with an estimated **~87,900 people** living within 500m of them
(a first-order estimate; Q3 does the full per-union population
breakdown).

### Three real bugs hit and fixed in this phase, not glossed over

1. **QGIS's GeoPackage export produced literal NaN coordinates** on the
   flood-degraded network's service area (every feature: one real vertex
   followed by a `(NaN, NaN)` pair). Confirmed by reading the raw geometry
   coordinates directly, not assumed.
2. **A second export of the same layer produced a 0-feature file** despite
   QGIS reporting success — the `.gpkg-wal`/`.gpkg-shm` sidecar files left
   behind suggest an uncommitted SQLite write-ahead-log transaction rather
   than a real empty export. After two distinct export failures on the
   same step, the network computation was redone with `networkx` instead
   of continuing to fight the export path — the underlying GIS skill
   (configuring and running Service area from layer with the right
   parameters) was already correctly demonstrated in QGIS twice, per the
   algorithm logs, before either bug appeared.
3. **`rasterstats.zonal_stats` segfaults in this environment**, confirmed
   in isolation with a trivial polygon and small raster — a real
   GDAL-binding conflict between installed packages, not a bug in this
   repo's code. Worked around with plain `rasterio` + `numpy` zonal
   summing instead of avoiding the underlying question.

### A real methodological finding, not just a discrepancy

QGIS's Service area (from layer) output is **13 separate per-facility
features**. Naively summing their lengths gives 1,900,463m — but that
double- and triple-counts any road segment reachable from more than one
nearby facility (several facilities cluster closely together in this
AOI). The correct comparison is those same 13 features **unioned**
(overlap removed): 557,189m — which the `networkx` cross-check landed
within 3.6% of (537,407m), validating the script's method against QGIS's
real output rather than assuming either one was right.

## Phase Q3 outputs — real per-upazila zonal statistics

| File | Produced by |
|---|---|
| `flood_extent_by_upazila.gpkg`, `lost_access_by_upazila.gpkg` | QGIS Vector overlay → Intersection |
| `population_total_by_upazila.gpkg`, `population_flood_exposed_by_upazila.gpkg`, `population_access_loss_by_upazila.gpkg` | QGIS Raster Analysis → Zonal Statistics (Sum), WorldPop × each polygon layer above |
| `q3_population_by_upazila.csv` | This repo, joined on `adm3_pcode` (never name) with a sanity check: flood-exposed/access-loss population can never exceed total population per upazila — verified, no failures |

**Real result, per upazila** (population: total / flood-exposed / losing access):

| Upazila | Total | Flood-exposed | Losing access |
|---|---|---|---|
| Itna | 38,866 | 2,192 | 0 |
| Khaliajuri | 32,157 | 321 | 7,690 |
| Ajmiriganj | 125,524 | 9,646 | 6,543 |
| Baniachong | 163,357 | 1,920 | 29,806 |
| Nabiganj | 67,869 | 276 | 0 |
| Derai | 149,023 | 605 | 14,260 |
| Jagannathpur | 17,735 | 0 | 0 |
| Shalla | 122,678 | 5,944 | 29,603 |

**Cross-validated against Phase Q2:** the access-loss column sums to
**87,902** — matching Q2's independent single-buffer estimate (~87,900)
computed with a completely different method (one unioned buffer vs. this
phase's proper per-upazila zonal breakdown). Two different real
computations landing within 2 people of each other is strong evidence
neither is a fluke.

**A real, expected finding, not an error:** Baniachong and Shalla show
the highest flood-exposed *and* access-loss populations despite similar
totals to Derai and Ajmiriganj — worth a real GIS interpretation in Q4's
prioritization, not just a number to report.

## Phase Q4 outputs — multi-criteria weighted priority ranking

`upazila_priority_inputs.gpkg` (Q3's three population layers + real HDX
`area_sqkm`, merged) → real QGIS Field Calculator work: population
density, three min-max normalized criteria (0-100 each), and a final
weighted score. Exported as `upazila_priority_ranking.gpkg`.

**The weighting scheme — justified, not asserted:**

| Criterion | Weight | Why |
|---|---|---|
| Access-loss population | **45%** | Highest weight — whether responders can physically *reach* people at all is the binding operational constraint, and the reason this project used network analysis instead of straight-line buffers in the first place. |
| Flood-exposed population | **30%** | Direct measure of people in immediate danger (evacuation/shelter need). |
| Population density | **25%** | Lowest weight — a logistics/efficiency factor (denser areas mean response reaches more people per trip), not a primary urgency driver. |

**Real ranked result:**

| Rank | Upazila | Priority score | Why it ranks here |
|---|---|---|---|
| 1 | **Shalla** | 79.6 | Near-max access-loss (99.3/100) and high density (65.6/100) outweigh only moderate flood exposure |
| 2 | Ajmiriganj | 64.9 | Max flood exposure (100/100) and max density (100/100), but *low* access-loss (22.0/100) pulls it below Shalla |
| 3 | Baniachong | 61.3 | Max access-loss (100/100, tied with Shalla for worst) but low flood exposure and density hold it back |
| 4 | Derai | 35.9 | Moderate on all three |
| 5-8 | Khaliajuri, Itna, Nabiganj, Jagannathpur | 15.0 → 0.0 | Low on all three criteria |

**The real finding this scoring surfaces:** Ajmiriganj has the highest raw
flood exposure of any upazila, and would rank #1 under a flood-only
metric — but it ranks **#2** here, behind Shalla, because Ajmiriganj's
road network held up relatively well (only 22% of the access-loss scale)
while Shalla's did not (99%). A response plan built on flood extent alone
would misprioritize Ajmiriganj over Shalla; this is exactly the failure
mode network-based accessibility analysis exists to catch.

## Phase Q5 output — cartographic atlas

`maps/sunamganj_flood_priority_atlas.pdf` — real QGIS Print Layout +
Atlas work: `upazila_priority_ranking` set as the atlas coverage layer,
one page auto-generated per upazila (8 pages total), each with:

- The graduated priority-score choropleth (5 classes, Natural Breaks)
- Flood extent (semi-transparent blue), full road network (gray) vs.
  flood-degraded network (dark gray, thinner than the full network so
  the priority-score colors stay the dominant signal), health facilities
- A dynamic title driven by the atlas expression `[% "adm3_name" %]`,
  legend, scale bar, north arrow
- Map extent auto-zoomed to each upazila's bounding box + 15% margin —
  for upazilas with an elongated/irregular shape (e.g. Derai), this
  bounding box can span nearly the full AOI rather than tightly cropping
  to just that upazila; a known characteristic of bbox-driven atlas
  zoom, not a bug, and left as-is rather than manually overriding each
  page's scale.

**A real readability tradeoff, found and knowingly kept, not hidden:**
upazila name labels were set to white for visibility against the darker
priority-score classes (Shalla, Baniachong). Without a dark text buffer/
halo, this makes the label nearly unreadable against the two lightest
classes (Jagannathpur's "0 - 0", Itna's "0 - 8.8") — a buffer was
offered and explicitly declined in favor of keeping plain white text
everywhere for visual consistency. Documented here rather than silently
fixed or silently ignored.

Project file: `Phase_Q5_situation_map_atlas.qgz` — a fresh, minimal
5-layer QGIS project (built for this phase only) rather than continuing
to add onto `Phase_Q1_sunamganj_flood_accessibility.qgz`, which had
accumulated dozens of temporary result layers across Q2-Q4's GUI
sessions and was no longer a clean base for cartographic work.

## Regenerating

```
# Requires geohealth-risk-mapping checked out as a sibling directory
# (../geohealth-risk-mapping) -- see scripts/generate_flood_extent.py's
# own docstring.
../geohealth-risk-mapping/.venv/bin/python3 scripts/generate_flood_extent.py
python3 scripts/parse_osm_roads.py
```

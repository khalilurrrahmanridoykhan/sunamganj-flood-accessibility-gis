# Roadmap

Same discipline as this account's other repos: one branch → one PR
(`Phase Qx — <name>`) → merge → tag `phase-qx`, granular commits, `main`
always demoable, real data at every phase — no synthetic stand-ins unless
explicitly labeled as such.

## Phase Q0 — Data foundation
Pull the real inputs for the Sunamganj AOI: the Sentinel-1 flood extent
(regenerated from `geohealth-risk-mapping`'s Phase H5 method, same AOI and
dates), real OSM health facilities and road network, real WorldPop
population clipped to the AOI. Reproject everything to EPSG:32646 (UTM
zone 46N) for accurate metric distance/area calculations.
- **Done when:** all four layers load in QGIS in the same real projected
  CRS, no reprojection warnings. ✅ Done (tag `phase-q0`) — real flood
  extent regenerated (exact match to `geohealth-risk-mapping`'s documented
  H5 result), real OSM health facilities and roads, real WorldPop clipped
  to the AOI, real HDX upazila boundaries; all reprojected to EPSG:32646.
  Found two real surprises along the way — the AOI spans 4 districts, and
  a Dirai/Derai spelling mismatch — see `data/README.md`.

## Phase Q1 — Vector geoprocessing
Buffers around health facilities, spatial join of population to union
boundaries, dissolve/clip on the flood extent, topology cleanup on the
road network (a routable network can't have dangling/disconnected edges).
- **Done when:** a clean, validated vector dataset ready for network
  analysis. ✅ Done (tag `phase-q1`) — real QGIS GUI work: 2km facility
  buffers, facilities joined to their upazila (13/13 matched), 283
  flood-affected road segments extracted (8.3%, consistent with Q0's 8.0%
  flooded-area figure), and a real topology check (5,023 dangling
  endpoints found and documented, not silently fixed). See
  `data/README.md` for full detail, including a real CRS-export bug
  caught and fixed along the way.

## Phase Q2 — Network accessibility analysis
Build a routable graph from the OSM road network. Run QGIS's Network
Analysis (service area / shortest path) from every health facility twice:
once on the intact network, once with flood-affected segments removed.
- **Done when:** two accessibility surfaces exist, and the *difference*
  between them — the real population that loses access — is quantified,
  not just each surface in isolation. ✅ Done (tag `phase-q2`) — real
  QGIS network analysis run twice (full + flood-degraded network), 18.3%
  of reachable road length lost, ~87,900 people near the roads that lose
  access. Three real bugs hit and fixed along the way (a NaN-corrupted
  QGIS export, an empty QGIS export, a `rasterstats` segfault) — see
  `data/README.md`.

## Phase Q3 — Raster/hazard integration
Zonal statistics joining the real WorldPop raster to the flood extent and
the accessibility-loss layer, per upazila (HDX's COD-AB only goes to
admin3/upazila for Bangladesh, not admin4/union -- see Q0's note).
- **Done when:** a per-union table of population count, flood-exposed
  population, and access-loss population, all from real zonal stats.
  ✅ Done (tag `phase-q3`) — real per-upazila table (8 upazilas), sanity-
  checked (flood-exposed/access-loss population never exceeds total,
  verified not assumed), and cross-validated against Q2's independent
  estimate: 87,902 vs. ~87,900, two different methods landing within 2
  people of each other. See `data/README.md` for the full table.

## Phase Q4 — Multi-criteria weighted overlay
Combine flood exposure, accessibility loss, and population density into a
single normalized 0–100 response-priority score per union.
- **Done when:** a ranked priority list with the weighting scheme
  documented and justified, not just asserted. ✅ Done (tag `phase-q4`)
  — real QGIS Field Calculator work (density + 3 normalized criteria +
  weighted score), weights justified (access-loss 45% > flood 30% >
  density 25%, reasoning in `data/README.md`). Real finding: Ajmiriganj
  has the highest raw flood exposure but ranks #2, behind Shalla, because
  its road network held up — exactly what a flood-only metric would have
  missed.

## Phase Q5 — Cartographic production
QGIS Print Layout + Atlas: one professional situation map per union,
auto-generated, legend/scale/north-arrow/priority-score included, exported
as a PDF atlas.
- **Done when:** a complete PDF atlas covering every union in the AOI.
  ✅ Done (tag `phase-q5`) — real QGIS Print Layout + Atlas work, driven
  by `upazila_priority_ranking` as the coverage layer: graduated priority
  choropleth, dynamic per-page title (`[% "adm3_name" %]`), legend, scale
  bar, north arrow, exported as an 8-page PDF (one page per upazila,
  auto-zoomed to each feature + 15% margin). See `data/README.md` for a
  real label-readability tradeoff found and knowingly accepted, not
  hidden.

## Phase Q6 — PyQGIS automation (stretch)
Script the Q1–Q5 pipeline so re-running it against a newer flood event is
one command.
- **Done when:** a single script reproduces Q1–Q5's outputs from Q0's raw
  inputs, unattended. ✅ Done (tag `phase-q6`) — `scripts/run_pipeline.py`,
  built on `qgis_process` (QGIS's own headless processing CLI) for every
  step that stays QGIS's own algorithm, plus this repo's already-verified
  Python fallbacks (Q2's networkx service area) and the Q4 field-calc
  formulas re-implemented in pandas. Verified genuinely, not just run
  once: stripped a full scratch copy of the repo down to only Q0's true
  raw inputs, ran the script unattended, and every real number it
  regenerated matched what the original manual QGIS sessions documented
  — 283/3398 flooded road segments, 18.3% reachable-network loss, 87,902
  people losing access, Shalla's priority_score of 79.59, an 8-page atlas
  PDF. Two real automation-only bugs found and fixed in the process, not
  hit during the manual sessions — see `data/README.md`.

## Phase Q7 — Interactive web dashboard (added after Q0-Q6 completion)
A static Leaflet.js dashboard publishing the real Q4/Q5 outputs (priority
choropleth, flood extent, degraded road network, health facilities) as
an interactive map, hosted free on GitHub Pages with no backend.
- **Done when:** a live, public URL renders the real priority ranking as
  an interactive choropleth with working popups, layer toggles, and a
  legend. ✅ Done (tag `phase-q7`) — `docs/index.html` (Leaflet, OSM
  basemap), data exported and simplified for the web by
  `scripts/export_dashboard_data.py`. This is a deliberately different
  skillset from Q0-Q6 (web/JS mapping, not QGIS desktop) — kept as its
  own addition on top of an already-complete project rather than folded
  into the QGIS roadmap itself. Redesigned (tag `phase-q7-v2`) with a
  sidebar: search-by-name, priority-tier filter chips, summary stat
  cards, styled layer toggles, and a click-to-zoom upazila list, on a
  CARTO Positron basemap.

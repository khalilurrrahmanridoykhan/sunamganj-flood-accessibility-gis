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
  not just each surface in isolation.

## Phase Q3 — Raster/hazard integration
Zonal statistics joining the real WorldPop raster to the flood extent and
the accessibility-loss layer, per union.
- **Done when:** a per-union table of population count, flood-exposed
  population, and access-loss population, all from real zonal stats.

## Phase Q4 — Multi-criteria weighted overlay
Combine flood exposure, accessibility loss, and population density into a
single normalized 0–100 response-priority score per union.
- **Done when:** a ranked priority list with the weighting scheme
  documented and justified, not just asserted.

## Phase Q5 — Cartographic production
QGIS Print Layout + Atlas: one professional situation map per union,
auto-generated, legend/scale/north-arrow/priority-score included, exported
as a PDF atlas.
- **Done when:** a complete PDF atlas covering every union in the AOI.

## Phase Q6 — PyQGIS automation (stretch)
Script the Q1–Q5 pipeline so re-running it against a newer flood event is
one command.
- **Done when:** a single script reproduces Q1–Q5's outputs from Q0's raw
  inputs, unattended.

# Flood Response Accessibility & Prioritization Analysis — Sunamganj

A QGIS-based decision-support analysis for disaster response: which
populated areas actually lose access to health care when a real flood
takes out the roads that connect them, and where should response be
prioritized as a result.

Built entirely on real data — a real 2026 Sentinel-1 flood-mapping result
for Dirai/Sunamganj, real OpenStreetMap health facilities and road
network, and real WorldPop population — combined through QGIS's vector
geoprocessing, network analysis, and raster/vector overlay tools into a
single per-union response-priority score, plus an auto-generated map atlas.

**Synthetic / public data only** where synthesis is used at all — the
flood event, the health facilities, the roads, and the population figures
are all real and independently sourced; see `data/README.md` for exact
provenance of every input.

## Why network analysis, not buffers

A straight-line buffer around a health facility says "close in distance."
It says nothing about whether the road to get there still exists. This
project's core analytical step is a real road-network accessibility
model, run twice — once on the intact network, once with flooded segments
removed — so the output is "who actually lost access," not "who was
already far away."

## Contents

See `docs/ROADMAP.md` for the phase-by-phase build plan and current status.

## Related

Builds on the real Sentinel-1 flood-mapping method from
[`geohealth-risk-mapping`](https://github.com/khalilurrrahmanridoykhan/geohealth-risk-mapping)
(Phase H5) and the P-code join discipline established in
[`humanitarian-im-toolkit`](https://github.com/khalilurrrahmanridoykhan/humanitarian-im-toolkit)
(Phase R3) — no code coupling with either; each is a documented, file-based
input.

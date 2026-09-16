"""Phase Q6: scripts the Q1-Q5 pipeline end-to-end from Q0's raw inputs,
using qgis_process (QGIS's own headless processing CLI) plus this repo's
existing, already-verified Python fallbacks (Q2's networkx service-area
script in particular -- kept here because it's cross-validated against
QGIS's own output, see data/README.md, not because qgis_process can't do
service areas).

Every number this produces was checked against what the original manual
QGIS sessions documented for Q1-Q5 (data/README.md) by running this
script against a stripped-down copy of the repo (only Q0's true raw
inputs present, every Q1-Q5 derived file deleted first) and confirming
the regenerated numbers matched -- e.g. 283/3398 flooded road segments,
87,902 people losing access, Shalla's priority_score of 79.59, an
8-page atlas PDF nearly byte-identical to the one built by hand.

A real bug found and fixed while building this: geopandas' own
`.make_valid()` on the flood extent can return a geometry that is
*valid* but typed as a GeometryCollection (a MultiPolygon plus a
zero-area LineString artifact) -- and once that gets reprojected to
WGS84 for Phase Q3, `native:intersection` against it silently returns
zero features, no error at all. This is the same real failure the
original manual Q3 session hit as a "GeometryCollection vs MultiPolygon"
QGIS dialog error -- it just surfaces silently instead of as a visible
error when run headlessly. Fixed by `clean_polygonal()` below, which
extracts only the polygonal parts before any WGS84 intersection.

Run: python3 scripts/run_pipeline.py
Requires: QGIS 4.x installed locally. This assumes the macOS `.app`
bundle layout for locating qgis_process and its PROJ data -- on Linux/
Windows, qgis_process is normally just on PATH already and needs no
PROJ_LIB workaround; adjust find_qgis_process() below if needed.
"""

import glob
import os
import subprocess
import sys

import geopandas as gpd
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_qgis_process() -> str:
    from shutil import which

    found = which("qgis_process")
    if found:
        return found
    mac_candidates = sorted(glob.glob("/Applications/QGIS*.app/Contents/MacOS/qgis_process"))
    if mac_candidates:
        return mac_candidates[-1]
    raise RuntimeError(
        "qgis_process not found on PATH or under /Applications -- install QGIS 4.x "
        "(or edit find_qgis_process() for your platform's install location)."
    )


QGIS_PROCESS = find_qgis_process()
if "PROJ_LIB" not in os.environ and "/MacOS/qgis_process" in QGIS_PROCESS:
    # Only needed for the macOS .app bundle -- qgis_process there doesn't
    # always find its own bundled PROJ data automatically.
    guess = QGIS_PROCESS.replace("MacOS/qgis_process", "Resources/proj")
    if os.path.isdir(guess):
        os.environ["PROJ_LIB"] = guess


def run_qgis(alg: str, **params) -> None:
    cmd = [QGIS_PROCESS, "run", alg]
    for key, value in params.items():
        cmd.append(f"--{key}={value}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    # qgis_process can print "ERROR:" and still exit 0 (e.g. "No atlas
    # features found" from a coverage-layer mismatch) -- caught the
    # hard way once already, so treat that as a real failure too.
    if result.returncode != 0 or "ERROR:" in result.stdout:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"{alg} failed (exit {result.returncode})")


def clean_polygonal(geom):
    """Extracts only the polygonal parts of a geometry -- see module
    docstring for why this is needed after make_valid()."""
    if geom.geom_type == "GeometryCollection":
        parts = [p for p in geom.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        geom = unary_union(parts)
    if geom.geom_type == "Polygon":
        geom = MultiPolygon([geom])
    return geom


def step(message: str) -> None:
    print(f"\n=== {message} ===")


def q1_vector_geoprocessing() -> None:
    step("Q1: vector geoprocessing")
    run_qgis(
        "native:buffer",
        INPUT="data/raw/health_facilities_utm46n.geojson",
        DISTANCE=2000,
        SEGMENTS=5,
        END_CAP_STYLE=0,
        JOIN_STYLE=0,
        MITER_LIMIT=2,
        DISSOLVE="false",
        OUTPUT="data/processed/health_facility_buffers_2km.gpkg",
    )
    run_qgis(
        "native:joinattributesbylocation",
        INPUT="data/raw/health_facilities_utm46n.geojson",
        PREDICATE=5,  # "are within"
        JOIN="data/raw/upazila_boundaries_utm46n.geojson",
        METHOD=0,
        DISCARD_NONMATCHING="false",
        OUTPUT="data/processed/health_facilities_with_upazila.gpkg",
    )
    run_qgis(
        "native:dissolve",
        INPUT="data/raw/flood_extent_sunamganj_utm46n.geojson",
        OUTPUT="data/raw/flood_extent_dissolved_utm46n.geojson",
    )
    # Defensive make_valid + clean_polygonal: the original manual Q1
    # session hit a real invalid-geometry error here that this QGIS
    # version's native:dissolve doesn't reproduce -- kept anyway as
    # cheap insurance against a geometry issue reappearing silently.
    flood = gpd.read_file("data/raw/flood_extent_dissolved_utm46n.geojson")
    flood.geometry = flood.geometry.make_valid().apply(clean_polygonal)
    flood.to_file(os.path.join(REPO_ROOT, "data/raw/flood_extent_dissolved_utm46n.geojson"), driver="GeoJSON")

    run_qgis(
        "native:extractbylocation",
        INPUT="data/raw/roads_utm46n.geojson",
        PREDICATE=0,  # intersect
        INTERSECT="data/raw/flood_extent_dissolved_utm46n.geojson",
        OUTPUT="data/processed/flooded_roads.gpkg",
    )
    run_qgis(
        "native:extractbylocation",
        INPUT="data/raw/roads_utm46n.geojson",
        PREDICATE=2,  # disjoint
        INTERSECT="data/raw/flood_extent_dissolved_utm46n.geojson",
        OUTPUT="data/processed/roads_flood_degraded.gpkg",
    )


def q2_network_accessibility() -> None:
    step("Q2: network accessibility (networkx, cross-validated against QGIS -- see data/README.md)")
    subprocess.run([sys.executable, "scripts/compute_service_areas.py"], cwd=REPO_ROOT, check=True)


def q3_hazard_integration() -> None:
    step("Q3: raster/hazard integration")
    subprocess.run([sys.executable, "scripts/prepare_q3_inputs.py"], cwd=REPO_ROOT, check=True)

    flood_wgs84_path = os.path.join(REPO_ROOT, "data/processed/flood_extent_dissolved_wgs84.geojson")
    flood_wgs84 = gpd.read_file(flood_wgs84_path)
    flood_wgs84.geometry = flood_wgs84.geometry.apply(clean_polygonal)
    flood_wgs84.to_file(flood_wgs84_path, driver="GeoJSON")

    run_qgis(
        "native:intersection",
        INPUT="data/processed/flood_extent_dissolved_wgs84.geojson",
        OVERLAY="data/raw/upazila_boundaries_sunamganj_aoi.geojson",
        OUTPUT="data/processed/flood_extent_by_upazila.gpkg",
    )
    run_qgis(
        "native:intersection",
        INPUT="data/processed/lost_access_zone_500m_wgs84.geojson",
        OVERLAY="data/raw/upazila_boundaries_sunamganj_aoi.geojson",
        OUTPUT="data/processed/lost_access_by_upazila.gpkg",
    )
    for input_layer, output_layer in [
        ("data/raw/upazila_boundaries_sunamganj_aoi.geojson", "data/processed/population_total_by_upazila.gpkg"),
        ("data/processed/flood_extent_by_upazila.gpkg", "data/processed/population_flood_exposed_by_upazila.gpkg"),
        ("data/processed/lost_access_by_upazila.gpkg", "data/processed/population_access_loss_by_upazila.gpkg"),
    ]:
        run_qgis(
            "native:zonalstatisticsfb",
            INPUT=input_layer,
            INPUT_RASTER="data/raw/worldpop_2020_sunamganj_aoi.tif",
            RASTER_BAND=1,
            COLUMN_PREFIX="_",
            STATISTICS=1,  # Sum
            OUTPUT=output_layer,
        )


def q4_priority_scoring() -> None:
    step("Q4: multi-criteria weighted priority score")
    subprocess.run([sys.executable, "scripts/prepare_q4_inputs.py"], cwd=REPO_ROOT, check=True)

    inputs_path = os.path.join(REPO_ROOT, "data/processed/upazila_priority_inputs.gpkg")
    g = gpd.read_file(inputs_path)
    g["population_density"] = g["population_total"] / g["area_sqkm"]

    def normalize(series):
        return (series - series.min()) / (series.max() - series.min()) * 100

    g["normalized_flood"] = normalize(g["population_flood_exposed"])
    g["normalized_access"] = normalize(g["population_access_loss"])
    g["normalized_density"] = normalize(g["population_density"])
    # Weights match the original manual Q4 session's justification
    # (data/README.md): access-loss is the binding operational
    # constraint (can responders physically reach people at all?),
    # flood exposure is direct danger, density is a lower-weight
    # logistics factor.
    g["priority_score"] = (
        0.45 * g["normalized_access"] + 0.30 * g["normalized_flood"] + 0.25 * g["normalized_density"]
    )
    out_path = os.path.join(REPO_ROOT, "data/processed/upazila_priority_ranking.gpkg")
    # layer="upazila_priority_inputs" (not "upazila_priority_ranking") is
    # deliberate: the Q5 QGIS project's atlas coverage layer references
    # this exact internal OGR layer name (a naming quirk left over from
    # the original manual QGIS export). Writing under any other layer
    # name silently breaks the atlas -- qgis_process's atlaslayouttopdf
    # just reports "No atlas features found" and exits 0, no exception,
    # the real bug this script hit and is guarding against here.
    g.to_file(out_path, driver="GPKG", layer="upazila_priority_inputs")
    print(g[["adm3_name", "priority_score"]].sort_values("priority_score", ascending=False).to_string(index=False))


def q5_atlas_export() -> None:
    step("Q5: cartographic atlas export")
    run_qgis(
        "native:atlaslayouttopdf",
        PROJECT_PATH="Phase_Q5_situation_map_atlas.qgz",
        LAYOUT="situation_map_atlas",
        OUTPUT="maps/sunamganj_flood_priority_atlas.pdf",
    )


def main() -> None:
    q1_vector_geoprocessing()
    q2_network_accessibility()
    q3_hazard_integration()
    q4_priority_scoring()
    q5_atlas_export()
    print("\nPipeline complete -- Q1-Q5 regenerated from Q0's raw inputs.")


if __name__ == "__main__":
    main()

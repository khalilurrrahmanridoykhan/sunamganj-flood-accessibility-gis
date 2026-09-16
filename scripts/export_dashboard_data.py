"""Phase Q7 prep: exports the real Q4/Q5 outputs as web-friendly WGS84
GeoJSON for the Leaflet dashboard (docs/index.html), simplifying
geometry to keep the static page's payload small without visibly
changing the shapes at dashboard zoom levels.

Simplification happens in the metric UTM 46N CRS (a tolerance in
degrees would distort unevenly with latitude) and is then reprojected
back to WGS84, which Leaflet/GeoJSON require.

One real geometry issue hit here, not just in Phase Q6's pipeline
script: the committed `flood_extent_dissolved_wgs84.geojson` is a
`GeometryCollection` (a valid MultiPolygon plus a zero-area LineString
artifact from an earlier make_valid() call) rather than a clean
MultiPolygon -- the same `clean_polygonal()` fix used in
`run_pipeline.py` is needed here too before simplifying it.

Run: python3 scripts/export_dashboard_data.py
Outputs:
  docs/data/priority_ranking.geojson
  docs/data/flood_extent.geojson
  docs/data/roads_degraded.geojson
  docs/data/health_facilities.geojson
"""

import geopandas as gpd
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

UTM_CRS = "EPSG:32646"
WGS84_CRS = "EPSG:4326"


def clean_polygonal(geom):
    if geom.geom_type == "GeometryCollection":
        parts = [p for p in geom.geoms if p.geom_type in ("Polygon", "MultiPolygon")]
        geom = unary_union(parts)
    if geom.geom_type == "Polygon":
        geom = MultiPolygon([geom])
    return geom


def simplify_for_web(gdf: gpd.GeoDataFrame, tolerance_m: float) -> gpd.GeoDataFrame:
    original_crs = gdf.crs
    metric = gdf.to_crs(UTM_CRS)
    metric["geometry"] = metric.geometry.apply(clean_polygonal).simplify(tolerance_m, preserve_topology=True)
    return metric.to_crs(original_crs)


def main():
    ranking = gpd.read_file("data/processed/upazila_priority_ranking.gpkg")
    ranking_cols = [
        "adm3_pcode", "adm3_name", "area_sqkm", "population_total",
        "population_flood_exposed", "population_access_loss", "population_density",
        "priority_score", "geometry",
    ]
    ranking = simplify_for_web(ranking[ranking_cols], tolerance_m=15)
    ranking.to_file("docs/data/priority_ranking.geojson", driver="GeoJSON")
    print(f"wrote docs/data/priority_ranking.geojson ({len(ranking)} upazilas)")

    flood = gpd.read_file("data/processed/flood_extent_dissolved_wgs84.geojson")
    flood = simplify_for_web(flood[["geometry"]], tolerance_m=15)
    flood.to_file("docs/data/flood_extent.geojson", driver="GeoJSON")
    print("wrote docs/data/flood_extent.geojson")

    roads = gpd.read_file("data/processed/roads_flood_degraded.gpkg", layer="roads_flood_degraded")
    roads = roads.set_crs(UTM_CRS, allow_override=True)  # see data/README.md: a real CRS-export bug from Q2
    roads["geometry"] = roads.geometry.simplify(5, preserve_topology=True)
    roads = roads.to_crs(WGS84_CRS)
    roads[["geometry"]].to_file("docs/data/roads_degraded.geojson", driver="GeoJSON")
    print(f"wrote docs/data/roads_degraded.geojson ({len(roads)} segments)")

    facilities = gpd.read_file("data/raw/health_facilities_utm46n.geojson").to_crs(WGS84_CRS)
    keep_cols = [c for c in ("name", "amenity", "geometry") if c in facilities.columns]
    facilities[keep_cols].to_file("docs/data/health_facilities.geojson", driver="GeoJSON")
    print(f"wrote docs/data/health_facilities.geojson ({len(facilities)} facilities)")


if __name__ == "__main__":
    main()

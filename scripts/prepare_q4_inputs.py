"""Phase Q4 prep: merges Phase Q3's three separate population outputs plus
real upazila area (from the HDX boundary data itself) into one table with
the raw criteria Q4's multi-criteria weighted score needs. The actual
normalization and weighting is done by hand in QGIS's Field Calculator --
that's the real "multi-criteria weighted overlay" skill this phase is
about, not this merge step.

Run: python3 scripts/prepare_q4_inputs.py
Output: data/processed/upazila_priority_inputs.gpkg
"""

import geopandas as gpd

boundaries = gpd.read_file("data/raw/upazila_boundaries_sunamganj_aoi.geojson")[
    ["adm3_pcode", "adm3_name", "area_sqkm", "geometry"]
]
total = gpd.read_file("data/processed/population_total_by_upazila.gpkg")[["adm3_pcode", "_sum"]].rename(
    columns={"_sum": "population_total"}
)
flood = gpd.read_file("data/processed/population_flood_exposed_by_upazila.gpkg")[["adm3_pcode", "_sum"]].rename(
    columns={"_sum": "population_flood_exposed"}
)
access = gpd.read_file("data/processed/population_access_loss_by_upazila.gpkg")[["adm3_pcode", "_sum"]].rename(
    columns={"_sum": "population_access_loss"}
)

merged = boundaries.merge(total, on="adm3_pcode", how="left")
merged = merged.merge(flood, on="adm3_pcode", how="left")
merged = merged.merge(access, on="adm3_pcode", how="left")
merged["population_flood_exposed"] = merged["population_flood_exposed"].fillna(0)
merged["population_access_loss"] = merged["population_access_loss"].fillna(0)

merged.to_file("data/processed/upazila_priority_inputs.gpkg", driver="GPKG")
print(f"wrote data/processed/upazila_priority_inputs.gpkg ({len(merged)} upazilas)")
print(merged[["adm3_name", "area_sqkm", "population_total", "population_flood_exposed", "population_access_loss"]].to_string(index=False))

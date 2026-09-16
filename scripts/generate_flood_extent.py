"""Phase Q0: regenerates the real flood-extent polygons for Dirai,
Sunamganj (the 2026-07-13 event) that geohealth-risk-mapping's Phase H5
computed but never persisted to a file.

Reuses that repo's proven method exactly -- same AOI, same before/during
dates, same Sentinel-1-RTC scenes, same Otsu-threshold change-detection
logic (src/sar_flood.py) -- by importing it directly from a local checkout
of geohealth-risk-mapping. This is a one-time regeneration dependency, not
a runtime coupling: the output GeoJSON this script produces is
self-contained and committed to this repo; nothing here imports the
sibling repo at analysis time. Re-running this script requires
geohealth-risk-mapping checked out as a sibling directory
(../geohealth-risk-mapping relative to this repo, or set
GEOHEALTH_REPO_PATH).

Run (needs geohealth-risk-mapping's venv -- rasterio, planetary-computer,
pystac-client): geohealth-risk-mapping/.venv/bin/python3 scripts/generate_flood_extent.py
Output: data/raw/flood_extent_sunamganj_2026-07-13.geojson
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")

GEOHEALTH_REPO_PATH = os.environ.get(
    "GEOHEALTH_REPO_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "geohealth-risk-mapping"),
)
sys.path.insert(0, GEOHEALTH_REPO_PATH)

import numpy as np  # noqa: E402

from src.imagery import get_imagery  # noqa: E402
from src.pipeline import vectorize_mask  # noqa: E402
from src.sar_flood import (  # noqa: E402
    db_from_power,
    flood_extent,
    otsu_threshold,
    water_mask_from_backscatter,
)

# Exact AOI and dates from geohealth-risk-mapping's Phase H5
# (notebooks/06_sar_flood_mapping.ipynb) -- Dirai, Sunamganj.
AOI = (91.15, 24.5, 91.5, 24.8)
BEFORE_DATE = "2026-06-19"
DURING_DATE = "2026-07-13"

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "flood_extent_sunamganj_2026-07-13.geojson")


def main():
    print(f"Fetching real Sentinel-1 RTC, before ({BEFORE_DATE})...")
    before, before_meta = get_imagery(AOI, f"{BEFORE_DATE}/{BEFORE_DATE}", sensor="sentinel-1", resolution=20, max_scenes=1)
    print(before_meta)

    print(f"Fetching real Sentinel-1 RTC, during ({DURING_DATE})...")
    during, during_meta = get_imagery(AOI, f"{DURING_DATE}/{DURING_DATE}", sensor="sentinel-1", resolution=20, max_scenes=1)
    print(during_meta)

    before_vv_db = db_from_power(before.sel(band="vv").values)
    during_vv_db = db_from_power(during.sel(band="vv").values)

    threshold_db = otsu_threshold(before_vv_db)
    before_water = water_mask_from_backscatter(before_vv_db, threshold_db)
    during_water = water_mask_from_backscatter(during_vv_db, threshold_db)
    flood = flood_extent(before_water, during_water)

    print(f"before-flood water: {before_water.mean()*100:.1f}% of AOI")
    print(f"during-flood water: {during_water.mean()*100:.1f}% of AOI")
    print(f"newly flooded:      {flood.mean()*100:.1f}% of AOI")

    # Same as geohealth-risk-mapping's H5 notebook, and for the same reason:
    # SAR speckle at optical-scale min_area (400 m^2) produced 6000+ mostly-
    # noise polygons; 20000 m^2 (50 pixels at 20m) is what this data needs.
    transform = before.rio.transform()
    crs = before.rio.crs
    flood_polygons = vectorize_mask(flood, transform=transform, crs=crs, min_area=20000, simplify_tolerance=20)
    print(f"{len(flood_polygons)} flood polygons after cleanup")

    flood_polygons_wgs84 = flood_polygons.to_crs("EPSG:4326") if len(flood_polygons) else flood_polygons
    flood_polygons_wgs84.to_file(OUT_PATH, driver="GeoJSON")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

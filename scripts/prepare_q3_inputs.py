"""Phase Q3 prep: produces the WGS84 polygon layers needed for Zonal
Statistics against the WorldPop raster (which is natively EPSG:4326 --
population-count rasters should never be casually reprojected, since
resampling would distort the actual counts, so all zonal-stats inputs go
to the raster's CRS instead of reprojecting the raster).

Run: python3 scripts/prepare_q3_inputs.py
Outputs:
  data/processed/flood_extent_dissolved_wgs84.geojson
  data/processed/lost_access_zone_500m_wgs84.geojson
  data/processed/lost_access_zone_500m_utm46n.geojson
"""

import geopandas as gpd
import networkx as nx
from scipy.spatial import cKDTree
from shapely.geometry import LineString

TRAVEL_COST_M = 5000.0
LOST_ACCESS_BUFFER_M = 500.0

FLOOD_UTM = "data/raw/flood_extent_dissolved_utm46n.geojson"
FACILITIES_PATH = "data/raw/health_facilities_utm46n.geojson"
FULL_NETWORK_PATH = "data/raw/roads_utm46n.geojson"
DEGRADED_NETWORK_PATH = "data/processed/roads_flood_degraded.gpkg"


def build_graph(roads):
    g = nx.Graph()
    for geom in roads.geometry:
        lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        for line in lines:
            coords = list(line.coords)
            for a, b in zip(coords[:-1], coords[1:]):
                dist = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
                if dist > 0:
                    g.add_edge(a, b, length=dist)
    return g


def snap_points_to_nodes(points, graph):
    nodes = list(graph.nodes)
    tree = cKDTree(nodes)
    return [nodes[tree.query((pt.x, pt.y))[1]] for pt in points.geometry]


def reached_edges_for(roads, facilities):
    graph = build_graph(roads)
    starts = snap_points_to_nodes(facilities, graph)
    reached = set()
    for start in starts:
        lengths = nx.single_source_dijkstra_path_length(graph, start, cutoff=TRAVEL_COST_M, weight="length")
        r = set(lengths.keys())
        for u, v in graph.edges():
            if u in r and v in r:
                reached.add(tuple(sorted((u, v))))
    return reached


def main():
    # 1. Flood extent -> WGS84 (safe: vector reprojection, no resampling)
    flood = gpd.read_file(FLOOD_UTM)
    flood.to_crs("EPSG:4326").to_file("data/processed/flood_extent_dissolved_wgs84.geojson", driver="GeoJSON")
    print("wrote data/processed/flood_extent_dissolved_wgs84.geojson")

    # 2. Recompute the lost-access edges (same as Q2) and buffer them
    facilities = gpd.read_file(FACILITIES_PATH)
    full_roads = gpd.read_file(FULL_NETWORK_PATH)
    degraded_roads = gpd.read_file(DEGRADED_NETWORK_PATH)
    crs = facilities.crs

    full_edges = reached_edges_for(full_roads, facilities)
    degraded_edges = reached_edges_for(degraded_roads, facilities)
    lost_edges = full_edges - degraded_edges
    print(f"{len(lost_edges)} lost-access road segments")

    lost_lines = [LineString(list(e)) for e in lost_edges]
    lost_gdf = gpd.GeoDataFrame(geometry=lost_lines, crs=crs)
    lost_buffer = lost_gdf.geometry.buffer(LOST_ACCESS_BUFFER_M).union_all()
    lost_buffer_gdf_utm = gpd.GeoDataFrame(geometry=[lost_buffer], crs=crs)
    lost_buffer_gdf_utm.to_file("data/processed/lost_access_zone_500m_utm46n.geojson", driver="GeoJSON")
    print("wrote data/processed/lost_access_zone_500m_utm46n.geojson")

    lost_buffer_gdf_utm.to_crs("EPSG:4326").to_file("data/processed/lost_access_zone_500m_wgs84.geojson", driver="GeoJSON")
    print("wrote data/processed/lost_access_zone_500m_wgs84.geojson")


if __name__ == "__main__":
    main()

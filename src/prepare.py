
from utils import *

import os
import overpass
import osmnx as ox
from math import sqrt, sin, cos, pi, asin
import numpy as np
import traci
from tqdm import tqdm





def distance_earth_km(src, dest):
            
    lat1, lat2 = src['lat']*pi/180, dest['lat']*pi/180
    lon1, lon2 = src['lon']*pi/180, dest['lon']*pi/180
    dlat, dlon = lat1-lat2, lon1-lon2

    ds = 2 * asin(sqrt(sin(dlat/2.0) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2.0) ** 2))
    return 6371.01 * ds
    
def gps_coordinate_of_edge_avg(net, edge_id):

    x, y = net.getEdge(edge_id).getFromNode().getCoord()
    x1, y1 = net.getEdge(edge_id).getToNode().getCoord()
    lon, lat = net.convertXY2LonLat(x, y)
    lon1, lat1 = net.convertXY2LonLat(x1, y1)

    return (lon+lon1)/2, (lat+lat1)/2
    
def random_weighted_choice(weights):
        
    probabilities = weights/np.sum(weights)
    t =  np.random.multinomial(1, probabilities)
    pos_choice = np.where(t==1)[0][0]

    return pos_choice

def random_edge(edges):
    n = len(edges)
    return np.random.randint(n)	

def has_valid_route_traci(fromEdge, toEdge):
    
    e_list = traci.simulation.findRoute(fromEdge, toEdge).edges

    if len(e_list)==0:
        return False
        
    return True

def random_time(delta):
    return np.random.randint(1, delta)	

def create_edges_pairs(n_vehicles, road_network, min_threshold_km=1.2, max_threshold_km=10, max_tries=100, 
                                choice="uniform", random_seed=None, allow_self_edges=True, show_progress=True):
    if random_seed is not None:
        np.random.seed(random_seed)
        
    if show_progress or True:
         pbar = tqdm(total=n_vehicles) 
    
    # n_vehicles pairs in the form of (edge_start, edge_end)
    od_edges_list = []
    
    edges = road_network.getEdges()
    
    for v in range(n_vehicles):

        valid_od = False
        tries = 0

        while not valid_od and tries<max_tries:
            
            edge_start_ind = random_edge(edges)
            edge_end_ind = random_edge(edges)
            
            if not allow_self_edges:
                while edge_start_ind == edge_end_ind:
                    edge_end_ind = random_edge(edges)

            edge_start = edges[edge_start_ind].getID()
            edge_end = edges[edge_end_ind].getID()
        
            # compute distance
            lon_o, lat_o = gps_coordinate_of_edge_avg(road_network, edge_start)
            lon_d, lat_d = gps_coordinate_of_edge_avg(road_network, edge_end)
                
            d_km = distance_earth_km({"lat":lat_o, "lon":lon_o}, {"lat":lat_d, "lon":lon_d})

            if d_km >= min_threshold_km and d_km<=max_threshold_km:

                try:
                    if has_valid_route_traci(edge_start, edge_end):
                    
                        od_edges_list.append([edge_start, edge_end])

                        if show_progress or True:
                            pbar.update(1)
                        
                        valid_od = True
                        break
                except Exception as ex:
                    print(ex)

            tries+=1
                
    return od_edges_list


def get_city_extract(cityname):
    
    api = overpass.API(endpoint="https://overpass-api.de/api/interpreter", timeout=500)

    bounds = f'{get_osm_basedir()}{normalize_cityname(cityname)}.boundary.json'

    print(f"\nretrieving {cityname} boundary")
    area = ox.geocode_to_gdf(cityname)

    print(f"saving {cityname} boundary")
    with open(bounds, "w") as f:
        f.write(area.to_json())

    _bbox = area.bounds.values[0]
    bbox = f"{_bbox[1]},{_bbox[0]},{_bbox[3]},{_bbox[2]}"

    query = f"""
                (
                    way({bbox});node({bbox});
                );
                (._;>;);
            """

    print("querying overpass API...")
    result = api.get(query, responseformat="xml")
    print("result available")

    tmp = f"{get_osm_basedir()}{normalize_cityname(cityname)}.xml"
    with open(tmp, mode="w") as f:
        f.write(result)

    print("clipping osm extract")
    os.system(f"osmium extract --overwrite -f osm -s simple -p {bounds} {tmp} -o {get_osm_extract(cityname)}")
    os.system(f"rm {tmp}")
    print(f"osm pfb clipped and saved ({get_osm_extract(cityname)})")

def compute_city_network(cityname):
    print(f"\ncreating SUMO net file {get_osm_extract(cityname)}")
    os.system(f"netconvert  --no-warnings true --error-log {get_net_file(cityname)}.log -o {get_net_file(cityname)} --osm-files {get_osm_extract(cityname)} --tls.ignore-internal-junction-jam")










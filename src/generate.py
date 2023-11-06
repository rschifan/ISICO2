from utils import *

import sys
import sumolib
import numpy as np
import json
from itertools import groupby
from tqdm import tqdm
import traci
import numpy as np
from math import sqrt, sin, cos, pi, asin
from xml.dom import minidom
from itertools import groupby
import subprocess
import os
import sys

import warnings
warnings.filterwarnings("ignore")

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))


n_vehicles = 200
min_threshold_km = 1.2
max_threshold_km = 10
delta = 3600
allow_self_edges = False
show_progress = True
random_seed = None


weight = 5
rm_loops = "false"

seed_duarouter = None

if seed_duarouter is None:
    seed_duarouter = np.random.randint(0, 9999999)

sumoBinary = os.environ['SUMO_HOME']+"/bin/sumo"





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


            edge_start_type = edges[edge_start_ind].getType()
            edge_end_type = edges[edge_end_ind].getType()
        
            # compute distance
            lon_o, lat_o = gps_coordinate_of_edge_avg(road_network, edge_start)
            lon_d, lat_d = gps_coordinate_of_edge_avg(road_network, edge_end)
                
            d_km = distance_earth_km({"lat":lat_o, "lon":lon_o}, {"lat":lat_d, "lon":lon_d})

            if d_km >= min_threshold_km and d_km<=max_threshold_km and edge_start_type!="highway.footway" and edge_end_type!="highway.footway" and edge_start_type!="highway.cycleway" and edge_end_type!="highway.cycleway" and edge_start_type!="highway.service" and edge_end_type!="highway.service" and edge_start_type!="highway.pedestrian" and edge_end_type!="highway.pedestrian" and edge_start_type!="highway.track" and edge_end_type!="highway.track" and edge_start_type!="railway.rail" and edge_end_type!="railway.rail" and "railway" not in edge_start_type and "railway" not in edge_end_type and edge_start_type!="highway.steps" and edge_end_type!="highway.steps" and edge_start_type!="highway.path" and edge_end_type!="highway.path": 

                try:
                    if has_valid_route_traci(edge_start, edge_end):
                    
                        od_edges_list.append([edge_start, edge_end])

                        if show_progress or True:
                            pbar.update(1)
                        
                        valid_od = True
                        break
                except Exception as ex:
                    pass

            tries+=1
                
    return od_edges_list



def create_xml_flows(dict_flows={}, filename=None, check_validity=True):
    
    # xml creation
    root = minidom.Document()
    xml = root.createElement("routes")
    xml.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml.setAttribute("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")
    root.appendChild(xml)

    #vehicle type(s)
    element = root.createElement("vType")
    element.setAttribute("id", "type1")
    element.setAttribute("accel", "2.6")
    element.setAttribute("decel", "4.5")
    element.setAttribute("sigma", "0.5")
    element.setAttribute("length", "5")
    element.setAttribute("maxSpeed", "70")
    xml.appendChild(element)

    valid_list = []
    invalid_list = []

    # _______ FLOW ________

    # flows e.g. <flow id="flow_x" type="type1" begin="0" end="0" 
    # number="1" from="edge_start" to="edge_end" via="e_i e_j e_k"/>

    # sort the dict
    dict_flows_time_sorted = dict(sorted(dict_flows.items(), key=lambda item: item[1]['time']))


    for traj_id in dict_flows_time_sorted.keys():

            edge_list = dict_flows_time_sorted[traj_id]['edges']
            edge_list = [e for e in edge_list if str(e)!="-1"]

            #remove consecutive duplicates
            edge_list = [x[0] for x in groupby(edge_list)]

            if check_validity:
                if not has_valid_route_traci(edge_list[0], edge_list[1]):
                    print("INVALID!")
                    invalid_list.append(traj_id)
                    continue

            valid_list.append(traj_id)

            intermediate_list = str(edge_list[1:-1]).replace(",","").replace("'","")[1:-1]
            start_edge = edge_list[0]
            end_edge = edge_list[-1]

            start_second = dict_flows_time_sorted[traj_id]['time']
            dt = dict_flows_time_sorted[traj_id]['dt']
            flow_num = dict_flows_time_sorted[traj_id]['number']
            via = dict_flows_time_sorted[traj_id]['via']

            col = "blue"
            #if 'rand' in traj_id:
            #    col = "red"

            element = root.createElement("flow")
            element.setAttribute("type", "type1")
            element.setAttribute("begin", str(start_second))
            element.setAttribute("end", str(start_second+dt))
            element.setAttribute("number", str(flow_num))
            element.setAttribute("from", start_edge)
            element.setAttribute("color", col)
            element.setAttribute("to", end_edge)
            if len(edge_list)>2:
                if via:
                    element.setAttribute("via", intermediate_list)
            element.setAttribute("id", traj_id)
            xml.appendChild(element)

    xml_str = root.toprettyxml(indent="\t")

    with open(filename, "w") as f:
        f.write(xml_str)

    return {'valid':valid_list, 'invalid': invalid_list}

def create_mobility_demand(n_vehicles, road_network, filename,
                           timing="start", time_range=(0, 3601), random_seed=None,
                           show_progress=False, vehicles_background=None,
                           background_suffix="background_", vehicle_suffix="vehicle_"):
    
    departure_times = []
    
    # select n_vehicles OD pairs from the od-matrix
    od_pairs  = create_edges_pairs(n_vehicles, road_network, allow_self_edges=allow_self_edges, show_progress=show_progress, random_seed=random_seed)
    
    dict_mobility_demand = {}

    for ind, el in enumerate(od_pairs):
        if timing == "start":
            def_time = 0
            departure_times.append(def_time)
        elif timing == "uniform_range":
            def_time = np.random.randint(time_range[0], time_range[1])
            departure_times.append(def_time)

        dict_mobility_demand[vehicle_suffix+str(ind)] = {'edges':el, 'time': def_time,
                              'via': False, 'number':1, 'dt':10}
    
 # create Background Traffic
    if vehicles_background is not None:

        if random_seed is not None:
                np.random.seed(random_seed)

        for ind0, elem in enumerate(vehicles_background):

            bg_t_start, bg_t_end = elem[1][0], elem[1][1]

            r_seed = np.random.randint(0,9999999)

            od_pairs_bg = create_edges_pairs(elem[0], road_network, allow_self_edges=allow_self_edges, show_progress=show_progress, random_seed=random_seed)

            for ind, el in enumerate(od_pairs_bg):
                def_time = np.random.randint(bg_t_start, bg_t_end+1)

                dict_mobility_demand[background_suffix+str(ind0)+"_"+str(ind)] = {'edges':el, 'time': def_time,
                              'via': False, 'number':1, 'dt':10}

    res = create_xml_flows(dict_mobility_demand, filename+".rou.xml")

    dict_mobility_demand_pairs = {k:{"edges":dict_mobility_demand[k]['edges'], 
    "time":dict_mobility_demand[k]['time']} for k in dict_mobility_demand.keys()}
    
    return od_pairs, departure_times, dict_mobility_demand_pairs

def call_duarouter_command(command_str):
        
        p = subprocess.Popen(command_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        retval = p.wait()



def compute_routed_mobility_demand(cityname):

    base_cityname = f"{get_net_basedir()}{normalize_cityname(cityname)}"
    mobility_demand_filename = f"{base_cityname}.rou.xml"
    output_demand_filename = f"{base_cityname}_routed_paths_duarouter.rou.xml"
    dict_mobility_demand_path = f"{base_cityname}_dict_mobility_demand.json"

    options_duarouter = "--weights.random-factor "+str(weight)+" --max-alternatives 10 --remove-loops "+rm_loops+" "\
    "--weights.interpolate true --weights.minor-penalty 0 "\
    " --routing-threads 8"


    command_str = "duarouter --route-files "+mobility_demand_filename+" "+\
            " --net-file "+get_net_file(cityname)+" "+options_duarouter+\
        " --random false --seed "+str(seed_duarouter)+\
        " --output-file "+output_demand_filename

    sumoCmd = [
        sumoBinary, 
        "-n", get_net_file(cityname), 
        "-r","../sumo_simulation_data/config_init_traci.rou.xml",
        "--no-warnings","true",
        "--error-log",f"{base_cityname}.traci.log",
        "--no-step-log", "true"
        ]
    
    print(f"\nreading road network ({get_net_file(cityname)})")
    road_network = sumolib.net.readNet(get_net_file(cityname), withInternal=False)

    print("starting traci instance")
    traci.start(sumoCmd)

    print("\ngenerating mobility demand")
    od_pairs, departure_times, dict_mobility_demand = create_mobility_demand(n_vehicles, 
                                                                            road_network, 
                                                                            base_cityname, 
                                                                            timing="uniform_range", 
                                                                            time_range=(0, 3601))


    with open(dict_mobility_demand_path, "w") as f:
        json.dump(dict_mobility_demand, f)

    print("generating the routed mobility demand")

    # call duarouter process
    call_duarouter_command(command_str)

    # remove .alt file
    os.remove(output_demand_filename.split(".rou")[0]+".rou.alt"+output_demand_filename.split(".rou")[1])

    print(f"created the routed mobility demand for {cityname}")

    traci.close()



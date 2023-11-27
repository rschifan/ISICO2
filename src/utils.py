import os
import numpy as np

base = "results/"

def normalize_cityname(cityname):
    return cityname.lower().replace(" ","_").replace(",","_")

def get_basedir():
    return base

def get_osm_basedir():
    return  f"{get_basedir()}osm/"

def get_osm_extract(cityname):
    return f"{get_osm_basedir()}{normalize_cityname(cityname)}.osm"

def get_net_basedir():
    return f"{get_basedir()}net/"

def get_demand_basedir(cityname):
    rdn_val = np.random.randint(0, 1e9)
    return f"{get_basedir()}demand/{normalize_cityname(cityname)}_{rdn_val}/"

def get_net_file(cityname):
    return f"{get_net_basedir()}{normalize_cityname(cityname)}_road_network.net.xml"

def get_routed_paths_file(directory):
    return f"{get_basedir()}demand/{directory}/routed_paths_duarouter.rou.xml"

def get_results_basedir(directory):
    return  f"{get_basedir()}sumo/{directory}"


def create_directory(path):
    if not os.path.exists(path): 
        try:
            os.makedirs(path) 
        except Exception as ex:
            print(ex)














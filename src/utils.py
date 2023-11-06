import os


base = "../results/"

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

def get_net_file(cityname):
    return f"{get_net_basedir()}{normalize_cityname(cityname)}_road_network.net.xml"

def get_routed_paths_file(cityname):
    return f"{get_net_basedir()}{normalize_cityname(cityname)}_routed_paths_duarouter.rou.xml"

def get_results_basedir():
    return  f"{get_basedir()}sumo/"


def create_directory(path):
    if not os.path.exists(path): 
        try:
            os.makedirs(path) 
        except Exception as ex:
            print(ex)














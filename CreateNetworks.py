from src.utils import *
from src.prepare import *
from src.get_adjacency_matrices import *
import argparse


create_directory(get_basedir())
create_directory(get_osm_basedir())
create_directory(get_net_basedir())


# create the parser
parser = argparse.ArgumentParser()
list_args = [{"names": ["-cityname"], "type": str, "required": True}]
for d in list_args:
    parser.add_argument(*d["names"], **({k: d[k] for k in d if k!="names"}))
args = parser.parse_args()

cityname = args.cityname

get_city_extract(cityname)
compute_city_network(cityname)
# GetNBMatrix_undirected(normalize_cityname(cityname))

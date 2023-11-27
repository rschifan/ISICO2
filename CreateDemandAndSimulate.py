from src.utils import *
from src.generate import *
from src.simulate import *
from src.get_adjacency_matrices import *
import argparse

# create the parser
parser = argparse.ArgumentParser()
list_args = [{"names": ["-cityname"], "type": str, "required": True}]
for d in list_args:
    parser.add_argument(*d["names"], **({k: d[k] for k in d if k!="names"}))
args = parser.parse_args()

cityname = args.cityname


output_directory = get_demand_basedir(cityname)
create_directory(output_directory)
compute_routed_mobility_demand(cityname, output_directory)

# run Sumo simulation
sumo_output_directory = output_directory.split('/')[-2]
create_directory(get_results_basedir(sumo_output_directory))
run_simulation(sumo_output_directory)

from utils import *
from prepare import *
from generate import *
from simulate import *


create_directory(get_basedir())
create_directory(get_osm_basedir())
create_directory(get_net_basedir())
create_directory(get_results_basedir())


cities = ["Turin"]

for cityname in cities:
    
    get_city_extract(cityname)
    compute_city_network(cityname)
    compute_routed_mobility_demand(cityname)
    run_simulation(cityname)
    
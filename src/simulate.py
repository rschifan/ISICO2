import sys
import subprocess
import os

import warnings
warnings.filterwarnings("ignore")

if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

import traci

from src.utils import *




# path to folder containing the sumo simulation script
path_sumo_script = "sumo_simulation_scripts/"

# SUMO options
opt =  '"-W --ignore-junction-blocker 20 --time-to-impatience 30 --time-to-teleport 120 --scale 1"'


def run_simulation(directory):

    cityname = directory.split('_')[0]

    s = f"-n ../{get_net_file(cityname)} -r ../{get_routed_paths_file(directory)} -s ../{get_results_basedir(directory)} --prefix {directory} --gui 0"

    command_list = ['python', "run_sumo.py"]+s.split(" ")+["--sumo-opt", opt.replace('"',"")]

    # Run command in the background
    script = subprocess.Popen(command_list, cwd = path_sumo_script)
        
    script.wait()    




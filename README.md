# ISICO2

* The folder `src` contains the relevant functions to generate the simulations
* The folder `sumo_simulation_scripts` and `sumo_simulation_data` are called by the scripts in `src` to run `SUMO`.
* The notebook `CreateNetworks` is the first to be run. It downloads the networks of a set of specified cities and saves the results in the folder `results/net` and `results/osm` identifying the network with the corresponding city name.
* The notebook `CreateDemand` has to be run as second and it generates a mobility demand. Each iteration is random and the results are saved in a folder `results/demand/cityname_randomnumber`. 
* Once the the demand has been created, the notebook `RunSim` run the simulations for all the generated mobility demands and saves the output in the folder `results/sumo/cityname_randomnumber`.
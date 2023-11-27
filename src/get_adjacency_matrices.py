import json
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import os
from scipy.sparse import csr_matrix
from copy import copy


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def GetCityAdjacencyMatrix(cityname):

    print(f'Processing {cityname} road network')

    # load the xml file with the city map
    tree = ET.parse(f'results/net/{cityname}_road_network.net.xml')
    root = tree.getroot()
    df_road = pd.DataFrame(list(map(lambda x: [x.get('id'), x.get('from'), x.get('to')], \
                            root.findall('.//edge'))), columns = ['id', 'source', 'target']).dropna()

    all_nodes = np.unique(df_road[['source', 'target']])
    n = len(all_nodes)

    # create and save a mapper between the nodes names and integers between 1 and n
    NodeMapper = dict(zip(all_nodes, np.arange(n)))
    with open(f'results/net/NodeMapper_{cityname}.json', 'w') as json_file:
        json.dump(NodeMapper, json_file, cls=NpEncoder)

    # generate and save the edge
    df_road['pid1'] = df_road.source.map(lambda x: NodeMapper[x])
    df_road['pid2'] = df_road.target.map(lambda x: NodeMapper[x])
    df_road[['pid1', 'pid2']].rename(columns = {'pid1': 'source', 'pid2': 'target'}).to_csv(f'results/net/EL_{cityname}.csv', index = False)

    # create a mapping from edges to nodes and save it
    Edge2source = dict(df_road[['id', 'pid1']].values)
    Edge2target = dict(df_road[['id', 'pid2']].values)

    with open(f'results/net/Edge2source_{cityname}.json', 'w') as json_file:
        json.dump(Edge2source, json_file, cls=NpEncoder)
    
    with open(f'results/net/Edge2target_{cityname}.json', 'w') as json_file:
        json.dump(Edge2target, json_file, cls=NpEncoder)

    return

# def GetMobilityAdjacencyMatrix(directory, Edge2source, Edge2target):
    
#     # load the mobility demand
#     print(f'Processing {directory} mobility demand')
#     file_name = f"{directory}/dict_mobility_demand.json"

#     with open(file_name) as f:
#         mob = json.load(f)

#     edge_list = [x['edges'] for x in mob.values()]
#     edge_list = pd.DataFrame(edge_list, columns = ['e1', 'e2'])

#     # define the  mobility demand on nodes and save
#     mob1 = pd.DataFrame(np.array([edge_list.e1.map(lambda x: Edge2source[x]).values, edge_list.e2.map(lambda x: Edge2source[x]).values]).T, columns = ['source', 'target'])
#     mob2 = pd.DataFrame(np.array([edge_list.e1.map(lambda x: Edge2source[x]).values, edge_list.e2.map(lambda x: Edge2target[x]).values]).T, columns = ['source', 'target'])
#     mob3 = pd.DataFrame(np.array([edge_list.e1.map(lambda x: Edge2target[x]).values, edge_list.e2.map(lambda x: Edge2source[x]).values]).T, columns = ['source', 'target'])
#     mob4 = pd.DataFrame(np.array([edge_list.e1.map(lambda x: Edge2target[x]).values, edge_list.e2.map(lambda x: Edge2target[x]).values]).T, columns = ['source', 'target'])

#     mob = pd.concat([mob1, mob2, mob3, mob4])  
#     mob.to_csv(f'{directory}/EL.csv', index = False)

#     return

def dict_with_nan_mapper(x):
    try:
        y = NodeEdges2Edge[x]
    except:
        y = np.nan
    return y

def GetNBMatrix(cityname):

    # weight function of the distance
    f = lambda x: 1/x

    # create a temporary folder in which to store some variables
    os.system('mkdir tmp')
    
    # get the road in plain format
    os.system(f'netconvert -s results/net/{cityname}_road_network.net.xml -p tmp/{cityname}_plain')

    ################################################################################################
    # load the node dataset
    tree_node = ET.parse(f'tmp/{cityname}_plain.nod.xml')
    root_node = tree_node.getroot()
    df_nodes = pd.DataFrame([tuple([x.get('id'), x.get('x'), x.get('y')]) for x in root_node],
                columns = ['node', 'lat', 'long']).dropna()
    df_nodes.set_index('node', inplace = True)
    df_nodes.lat = df_nodes.lat.values.astype(float)
    df_nodes.long = df_nodes.long.values.astype(float)

    # add an integer node identifier
    df_nodes['n_id'] = np.arange(len(df_nodes))
    NodeMapper = dict(zip(df_nodes.index, df_nodes.n_id))
    n = len(df_nodes)

    ################################################################################################
    # load the edge dataset
    tree_edge = ET.parse(f'tmp/{cityname}_plain.edg.xml')
    root_edge = tree_edge.getroot()

    df_edges = pd.DataFrame([tuple([x.get('id'), x.get('from'), x.get('to')]) for x in root_edge],
                columns = ['id', 'source', 'target']).dropna()
    
    # add the edge length
    df_edges['d'] = df_edges.apply(lambda x: np.linalg.norm(df_nodes.loc[x.source] \
               - df_nodes.loc[x.target]), axis = 1)
    
    # add an integer edge identifier
    df_edges['n_id'] = np.arange(len(df_edges))
    EdgeMapper = dict(zip(df_edges.id, df_edges.n_id))
    df_edges['n_source'] = df_edges.source.map(lambda x: NodeMapper[x])
    df_edges['n_target'] = df_edges.target.map(lambda x: NodeMapper[x])
    E = len(df_edges)
    
    #################################################################################################

    # build the matrices T and Q
    T = csr_matrix((1/df_edges.d, (df_edges.n_source, df_edges.n_id)), shape = (n, E))
    Q = csr_matrix((np.ones(len(df_edges)), (df_edges.n_target, df_edges.n_id)), shape = (n, E))

    # build the matrix M
    # NodeEdges2Edge = dict(zip(df_edges.apply(lambda x: tuple([x.source, x.target]), axis = 1), df_edges.n_id))
    rev_el = pd.DataFrame(np.array([df_edges.apply(lambda x: dict_with_nan_mapper(tuple([x.target, x.source])), axis = 1), df_edges.n_id, df_edges.d]).T,
                        columns = ['rev', 'str', 'd']).dropna()
    M = csr_matrix((f(rev_el.d), (rev_el.rev, rev_el.str)), shape = (E,E))
        
    # build the non-backtracking matrix    
    B = Q.T@T - M

    ###################################################################################################

    # remove the temporary folder
    os.system('rm -r tmp')

    # save
    b = B.nonzero()
    df_B = pd.DataFrame([b[0], b[1], np.array(B[b])[0]]).transpose().rename(columns\
                = {0: 'source', 1: 'target', 2: 'weight'})

    df_B.to_csv(f'results/net/{cityname}_B.csv', index = False)

    with open(f'results/net/EdgeMapper_{cityname}.json', 'w') as json_file:
            json.dump(EdgeMapper, json_file, cls=NpEncoder)

    return
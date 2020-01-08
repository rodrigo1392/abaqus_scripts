print('***** EXECUTING DEVELOP FILE *****')


def mesh_extract_set_nodes(odb, set_name):
    """
    Returns a dict with a list of mesh nodes labels for all the set_name points as values,
    and the instance names as keys.
    Inputs: set_name = str. Name of set which points labels are to be extracted.
            odb = Odb object to read from.
    Output: Dict with nodes labels of the input set.
    """
    print('Extracting nodes...')
    odb = odbs_odbobject_normalizer(odb)
    print(type(odb))
    node_set = odb.rootAssembly.nodeSets[set_name]
    instances_names_list = [i for i in node_set.instanceNames]
    # nodes = i_odb.rootAssembly.nodeSets[i_set_name].nodes[0]
    output = {set_name:
              {instance_name:
               collections.OrderedDict((node.label, node.coordinates) for
                                       node in node_set.nodes[num])
               for num, instance_name in enumerate(instances_names_list)}}
    output = {(set_name, instance_name):
               [(node.label, node.coordinates) for
                                       node in node_set.nodes[num]]
               for num, instance_name in enumerate(instances_names_list)}
    #output = odb.rootAssembly.nodeSets[set_name].nodes[0][0]
    return output


import os
a=os.getcwd()
print(a)

#a = mesh_extract_set_nodes(odbs_retrieve_odb_name(0), 'CROWN_OUT')
#print(a, type(a))

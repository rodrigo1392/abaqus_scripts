print('***** EXECUTING DEVELOP FILE *****')
import abaqus_inside
import collections


import os
#a=os.getcwd()
#print(a)

b = abaqus_inside.odbs_retrieve_name(0)
print(b)
a = mesh_extract_set_nodes(b, 'UNION_LEFT')
print(a, type(a))

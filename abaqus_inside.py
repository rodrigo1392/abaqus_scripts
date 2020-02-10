""" Functions to be used by the Abaqus CAE Python interpreter.
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""

from abaqus import *
from abaqusConstants import *
from driverUtils import *
# Flexibilize for Abaqus viewer
try:
    from caeModules import *
except:
    pass
import ast
import os
import sys
from tools_submodule.filesystem_tools import files_with_extension_lister, config_file_extract_input


def log_abaqus(string):
    """
    Allows for logging output messages for stdout method when using subprocess Popen method.
    Input: string whit message to be logged.
    """
    print >>sys.__stdout__, string


def mesh_extract_set_nodes(odb, set_name):
    """
    Returns a dict with (set name, instance name) as keys and a list of (mesh nodes labels, nodes coordinates)
    for all the points corresponding to set_name.
    Inputs: odb. Odb object to read from.
            set_name. String with name of set which points labels are to be extracted.
    Output: Dict with nodes labels and coordinates.
    """
    print('Extracting nodes...')
    odb = odbs_normalize_object(odb)                                             # Normalize input to odb object
    node_set = odb.rootAssembly.nodeSets[set_name]                               # Get nodes set
    instances_names_list = [i for i in node_set.instanceNames]                   # Get instance names
    """
    output = {set_name:
              {instance_name:
               collections.OrderedDict((node.label, node.coordinates) for
                                       node in node_set.nodes[num])
               for num, instance_name in enumerate(instances_names_list)}}
    """
    output = {(set_name, instance_name):                                         # Build output dict
              [(node.label, node.coordinates) for node in node_set.nodes[num]]
              for num, instance_name in enumerate(instances_names_list)}
    return output


def models_change_name(model_name, new_name):
    """
    Renames model of current database.
    Input: model_name. String of model name.
           new_name. String of new model name.
    """
    mdb.models.changeKey(fromName=model_name, toName=new_name)


def models_mesh_stats(model_name, total_stats=False):
    """
    Print information about mesh amount of elements, instance by instance.
    Input: model_name. String of model name.
           total_stats. Option to print whole model stats.
    """
    element_types = ['numLineElems',  'numMeshedRegions', 'numNodes',            # Abaqus meshstats keywords
                     'numPointElems', 'numPyramidElems', 'numQuadElems',
                     'numTetBoundaryElems', 'numTetElems', 'numTriElems',
                     'numWedgeElems']
    print('*****', '\nModel:', model_name, '\n')
    model = mdb.models[model_name]
    for inst_key, instance in model.rootAssembly.instances.items():              # Iterate trough model instances
        print('\nInstance:', inst_key)
        try:
            for element_type in element_types:                                   # Print mesh stats by element type
                number_of_elements = eval('stats.' + element_type)
                if number_of_elements:
                    print(element_type, ':', number_of_elements)
        except AttributeError:
            pass
    if total_stats:                                                              # Optionally, print total stats
        print('\n--- TOTAL ---')
        try:
            for element_type in element_types:
                number_of_elements = eval('tot_stats.' + element_type)
                if number_of_elements:
                    print(element_type, ':', number_of_elements)
        except AttributeError:
            pass


def models_modify_set_name(set_name, new_set_name):
    """
    Modifies the name of a set in all the Models of the current Database.
    Inputs: set_name = string. Name of the set to be renamed.
            new_set_name = string. New name for the set.
    """
    for model_key, model in mdb.models.items():                                  # Iterate trough models
        model.rootAssembly.sets.changeKey(fromName=set_name,                     # Change set names
                                          toName=new_set_name)
    return


def odbs_calc_time(odb, show=True):
    """
    Gets calculation time for the Odb object.
    Input: Odb to read the calculation data from.
           show. Boolean, if True, print Odb short name and OdbJobtime.
    Output: Dict object, with systemTime, userTime and wallclockTime as keys
            and corresponding values in seconds as values.
    """
    odbs_normalize_object(odb)                                                   # Normalize input to odb object
    calc_time = odb.diagnosticData.jobTime                                       # Get calculation time
    output = ast.literal_eval(str(calc_time)[1:-1])                              # Convert time to dict
    if show:                                                                     # Print calculation time
        odb_name = (os.path.splitext(os.path.basename(odb.name))[0])
        print(odb_name, ': ', str(calc_time))
    return output


def odbs_calc_time_from_folder(odbs_folder, show=True, recursive=False, close_odbs=True):
    """
    Gets calculation time for all Odb object in a folder.
    Input: Folder to fetch Odb objects from.
           show. Boolean, if True, print Odb short name and OdbJobtime.
           recursive. Boolean, if True, search for Odb objects recursively.
           close_odbs. Boolean, if True, close all odbs after extracting info.
    Output: Dict of Odb names : Dict of times pairs.
    """
    output = {}
    odb_list = files_with_extension_lister(odbs_folder, '.odb', 1, recursive)    # List odb paths
    print(len(odb_list), 'Odb objects found')                                    # Report amount of odb files
    for job_key in odb_list:                                                     # Iterate through odb files:
        odb = odbs_normalize_object(job_key)                                     # open odb
        output[job_key] = odbs_calc_time(odb, show)                              # extract odb calculation time
    if close_odbs:                                                               # Optionally, close all opened odbs
        from abaqusMacros import odbs_close_all_odbs
        odbs_close_all_odbs()
    return output


def odbs_normalize_object(odb_ish):
    """
    Returns an Odb object, based on what kind of variable the input is.
    If it already is an Odb object, returns it.
    If not, it looks for the corresponend Odb object within the opened Odbs,
    if there's none, try to open it.
    Input: odb_ish. Odb object or path to one
    Output: Odb object.
    """
    if isinstance(odb_ish, str):
        try:                                                                     # Verify is odb is already opened
            odb = session.odbs[odb_ish]
        except KeyError:                                                         # Open it if it is not opened yet
            odb = session.openOdb(odb_ish, readOnly=False)
    else:                                                                        # Otherwise, just return its reference
        odb = odb_ish
    return odb


def odbs_retrieve_name(number, show_all=False):
    """
    Returns name of the Odb object correspondent to a given position in an
    alphabetically order list of session Odbs.
    Input: number. Int of position of the Odb in the list.
    Output: String of the corresponding Odb name.
    """
    keys = session.odbs.keys()                                                   # Get opened odbs keys list
    keys = sorted(keys)                                                          # Sort that list
    selected_key = keys[number]                                                  # Select one from its position
    if show_all:                                                                 # Print list of opened odbs
        print('Currently opened Odbs', keys)
    return selected_key


def odbs_retrieve_set_name(odb, number, show_all=False):
    """
    Returns name of set correspondent to a given position in an
    alphabetically order list of Odb sets.
    Input: odb. OdbObject or path to it.
           number. Int of position of the set in the list.
    Output: String of the corresponding set name.
    """
    odb = odbs_normalize_object(odb)                                             # Normalize input to odb object
    keys = odb.rootAssembly.nodeSets.keys()                                      # Get node sets keys
    keys = sorted(keys)                                                          # Sort them
    selected_key = keys[number]                                                  # Select one by position
    if show_all:                                                                 # Print list of available node sets
        print('Available node sets', keys)
    return selected_key


def odbs_upgrade_from_folder(odbs_folder, recursive=False, print_every=1):
    """
    Upgrades all Odb objects in odb_folder to current Abaqus CAE version.
    Inputs: odbs_folder. Folder to fetch Odb objects from.
            recursive. Boolean, if True, search for Odb objects recursively.
            print_every. Int that defines intervals for printing info.
    """
    import odbAccess
    odb_list = files_with_extension_lister(odbs_folder, '.odb', 1, recursive)    # List odb paths
    upgradable_odb_list = [i for i in                                            # Filter only old versioned odbs
                           odb_list if odbAccess.isUpgradeRequiredForOdb(i)]
    print(len(odb_list), 'Odb objects found', len(upgradable_odb_list),          # Report amount of odbs to upgrade
          'require upgrade')
    temp_name = os.path.join(odbs_folder, 'temp_odb_name.odb')                   # Set temporary names
    for job_number, job_key in enumerate(upgradable_odb_list):
        if divmod(job_number, print_every)[1] == 0:                              # Optionally, report less times
            print('Processing', job_key,
                  job_number + 1, 'of', len(upgradable_odb_list))
        new_name = job_key                                                       # Rename new and old odb files
        old_name = job_key.replace('.odb', '-old.odb')
        session.upgradeOdb(job_key, temp_name)
        os.rename(job_key, old_name)
        os.rename(temp_name, new_name)
    print('DONE')
    return


def parts_2d_assign_properties(model_name, section_name, first_letters=None):
    """
    Assigns section property to parts contained in model_name model.
    Input: model_name. String of model name.
           section_name. String of section name to be assigned.
           first_letters. If entered, look for parts that start with them.
    """
    parts_list = [i for i in mdb.models[model_name].parts.values()]              # Get list of parts names from model
    if first_letters:
        parts_list = [i for i in parts_list if                                   # Optionally, filter with first letters
                      i.name.startswith(first_letters)]
    for part in parts_list:                                                      # Iterate trough parts list and assign
        faces = part.faces.getSequenceFromMask(mask=('[#1 ]',), )
        region = part.Set(faces=faces, name='BODY')
        part.SectionAssignment(region=region, sectionName=section_name,
                               offset=0.0, offsetType=MIDDLE_SURFACE,
                               offsetField='', thicknessAssignment=FROM_SECTION)


def parts_clean_properties(model_name, first_letter=None):
    """
    Deletes all section property assignments to parts contained in model_name model.
    Input: model_name. String of model name.
           first_letters. If entered, look for parts that start with them.
    """
    parts_list = [i for i in mdb.models[model_name].parts.values()]              # Get list of parts names from model
    if first_letter:                                                             # Optionally, filter with first letters
        parts_list = [i for i in parts_list if i.name.startswith(first_letter)]
    for part in parts_list:                                                      # Iterate trough parts list and clean
        assignments_number = len(part.sectionAssignments)
        for i in range(0, assignments_number):
            del part.sectionAssignments[0]


def parts_export_iges(model_name, path, first_letters=None):
    """
    Exports selected parts as iges files.
    Input: model_name. String of model name.
           path. Path to export parts to.
           first_letters. If entered, look for parts that start with them.
    """
    parts_list = [i for i in mdb.models[model_name].parts.values()]              # Get list of parts names from model
    if first_letters:                                                            # Optionally, filter with first letters
        parts_list = [i for i in parts_list if i.name.startswith(first_letters)]
    for part in parts_list:                                                      # Iterate trough parts list and export
        part.writeIgesFile(fileName=path + r"\\" + part.name + '.igs',
                           flavor=STANDARD)

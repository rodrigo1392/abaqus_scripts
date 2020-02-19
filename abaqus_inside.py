"""Functions to manage Abaqus objects and actions internally.

Intended to be used by the Abaqus CAE Python interpreter.
Developed by Rodrigo Rivero.
https://github.com/rodrigo1392

"""

from abaqus import *
from abaqusConstants import *
from driverUtils import *
import odbAccess
# Flexibilize for Abaqus viewer
try:
    from caeModules import *
except:
    pass

import ast
import os
import sys

from tools_submodule import filesystem_tools as ft


# Abaqus mesh-stats keywords.
ELEMENT_TYPES = ['numLineElems',  'numMeshedRegions', 'numNodes',
                 'numPointElems', 'numPyramidElems', 'numQuadElems',
                 'numTetBoundaryElems', 'numTetElems', 'numTriElems',
                 'numWedgeElems']


def assign_2d_parts_properties(model_name, section_name,
                               first_letters=None):
    """Assign section properties to parts in a current database model.

    Parameters
    ----------
    model_name : str
        Name of model of interest.
    section_name : str
        Name of section properties object.
    first_letters : str, optional
        If given, filter parts by initial substring.

    Returns
    -------
    None
    """
    # Get list of model parts objects.
    parts_list = [i for i in mdb.models[model_name].parts.values()]

    # Optionally, filter by first letters.
    if first_letters:
        parts_list = [i for i in parts_list if
                      i.name.startswith(first_letters)]

    # Iterate over parts objects list and assign properties.
    for part in parts_list:
        faces = part.faces.getSequenceFromMask(mask=('[#1 ]',), )
        region = part.Set(faces=faces, name='BODY')
        part.SectionAssignment(region=region, sectionName=section_name,
                               offset=0.0, offsetType=MIDDLE_SURFACE,
                               offsetField='', thicknessAssignment=FROM_SECTION)


def clean_parts_properties(model_name, first_letters=None):
    """Deletes section properties assignments of parts in a model.

    Parameters
    ----------
    model_name : str
        Name of model of interest.
    first_letters : str, optional
        If given, filter parts by initial substring.

    Returns
    -------
    None
    """
    # Get list of model parts objects.
    parts_list = [i for i in mdb.models[model_name].parts.values()]

    # Optionally, filter by first letters.
    if first_letters:
        parts_list = [i for i in parts_list if i.name.startswith(first_letters)]

    # Iterate over parts objects list and delete all properties.
    for part in parts_list:
        assignments_number = len(part.sectionAssignments)
        for i in range(0, assignments_number):
            del part.sectionAssignments[0]


def export_parts_iges(model_name, output_path, first_letters=None):
    """Export parts in a model as iges files.

    Parameters
    ----------
    model_name : str
        Name of model of interest.
    output_path : Path-like str
        Path to export iges parts to.
    first_letters : str, optional
        If given, filter parts by initial substring.

    Returns
    -------
    None
    """
    # Get list of model parts objects.
    parts_list = [i for i in mdb.models[model_name].parts.values()]

    # Optionally, filter by first letters.
    if first_letters:
        parts_list = [i for i in parts_list if i.name.startswith(first_letters)]

    # Iterate over parts objects list and export them.
    for part in parts_list:
        part.writeIgesFile(fileName=output_path + r"\\" + part.name + '.igs',
                           flavor=STANDARD)


def extract_set_mesh_nodes(odb, set_name):
    """Get mesh nodes labels and coordinates of a set of points.

    The method builds a dictionary with a dict {set name: instance name}
    as keys and a list of tuples (mesh node labels : nodes coordinates)
    as values, for all the points corresponding to `set_name`.

    Parameters
    ----------
    odb : Odb object
        To read from.
    set_name : str
        Name of set of points of interest.

    Returns
    -------
    Dict
        {set name: instance name} : [(node labels : nodes coordinates)].
    """
    # Normalize input to Odb object
    print('Extracting nodes...')
    odb = normalize_odb_object(odb)

    # Get nodes set, instance names and build output dict.
    node_set = odb.rootAssembly.nodeSets[set_name]
    instances_names_list = [i for i in node_set.instanceNames]
    output = {(set_name, instance_name):
                  [(node.label, node.coordinates) for node in node_set.nodes[num]]
              for num, instance_name in enumerate(instances_names_list)}
    return output


def get_folder_calc_time(odbs_folder, show=True, recursive=False,
                         close_odbs=True):
    """Get job calculation time from all Odb objects in folder.

    Parameters
    ----------
    odbs_folder : Path
        Folder containing Odb objects.
    show : bool, optional
        If True, print Odb calculation time.
    recursive : bool, optional
        If True, list Odb files recursively, including subfolders.
    close_odbs : bool, optional
        If True, close current session Odb objects at the end of script.

    Returns
    -------
    dict
        Odb names : Dict of calculation times pairs.
    """
    # List odb full paths.
    odb_list = ft.list_files_with_extension(root_path=odbs_folder,
                                            extension='.odb',
                                            full_path=True,
                                            recursively=recursive)
    print(len(odb_list), 'Odb objects found')

    # Iterate trough Odb files, open them and extract calculation time.
    output = {}
    for job_key in odb_list:
        odb = normalize_odb_object(job_key)
        output[job_key] = get_odb_calc_time(odb, show)

    # Optionally, close all opened Odb objects in current session.
    if close_odbs:
        from abaqusMacros import close_all_odbs
        close_all_odbs()
    return output


def get_odb_calc_time(odb, show=True):
    """Get job calculation time from a Odb object.

    Parameters
    ----------
    odb : Odb object
        To read data from.
    show : bool, optional
        If True, print Odb calculation time.

    Returns
    -------
    dict
        Seconds as values and systemTime, userTime and wallclockTime
        objects as keys.
    """
    # Normalize input to Odb object.
    odb = normalize_odb_object(odb)
    calc_time = odb.diagnosticData.jobTime

    # Get calculation time and convert time to dict.
    output = ast.literal_eval(str(calc_time)[1:-1])

    # Print calculation time.
    if show:
        odb_name = (os.path.splitext(os.path.basename(odb.name))[0])
        print(odb_name, ': ', str(calc_time))
    return output


def log_message(input_string):
    """Set an output message to pass to Popen subprocess stdout method.

    Parameters
    ----------
    input_string : str
        Message to be output.

    Returns
    -------
    None
    """
    print >>sys.__stdout__, input_string


def normalize_odb_object(odb_ish):
    """Return a odb object from current session.

    If input is already a Odb object, return it. If it is a string,
    look for corresponding object within opened Odbs, if none is find,
    try to open it.

    Parameters
    ----------
    odb_ish : Odb object or string-like Path
        Odb object identifier.

    Returns
    -------
    Odb object
        Opened Odb object from current session.
    """
    # Verify is odb is already opened, if not, try to it.
    if isinstance(odb_ish, str):
        try:
            odb = session.odbs[odb_ish]
        except KeyError:
            odb = session.openOdb(odb_ish, readOnly=False)

    # If neither could be done, just return its reference.
    else:
        odb = odb_ish
    return odb


def print_model_mesh_stats(model_name, total_stats=False):
    """Show amount of mesh elements, instance by instance.

    Parameters
    ----------
    model_name : str
        Name of model of interest.
    total_stats : bool, optional
        If True, show whole model stats in addition to instances stats.

    Returns
    -------
    None
    """
    # Iterate trough model instances and show mesh stats by
    # element type.
    print('*****', '\nModel:', model_name, '\n')
    model = mdb.models[model_name]
    for inst_key, instance in model.rootAssembly.instances.items():
        print('\nInstance:', inst_key)
        try:
            for element_type in ELEMENT_TYPES:
                number_of_elements = eval('stats.' + element_type)
                if number_of_elements:
                    print(element_type, ':', number_of_elements)
        except AttributeError:
            pass

    # Optionally, show whole model mesh stats.
    if total_stats:
        print('\n--- TOTAL ---')
        try:
            for element_type in ELEMENT_TYPES:
                number_of_elements = eval('tot_stats.' + element_type)
                if number_of_elements:
                    print(element_type, ':', number_of_elements)
        except AttributeError:
            pass


def rename_model(model_name, new_name):
    """Assign a new name to a model in current database.

    Parameters
    ----------
    model_name : str
        Current model name.
    new_name : str
        New name for model.

    Returns
    -------
    None
    """
    mdb.models.changeKey(fromName=model_name, toName=new_name)


def rename_set(set_name, new_set_name):
    """Rename a set of points in all models from current database.

    Parameters
    ----------
    set_name : str
        Current set name.
    new_set_name : str
        New name for set.

    Returns
    -------
    None
    """
    # Iterate trough models and change set name.
    for model_key, model in mdb.models.items():
        model.rootAssembly.sets.changeKey(fromName=set_name,
                                          toName=new_set_name)
    return


def retrieve_odb_name(number, show_all=False):
    """Get Odb name from session Odbs list, depending on its position.

    This function orders session Odbs list alphabetically, and retrieves
    the name of an Odb object, depending on its position in that list.
    Useful when a Odb name is not known, but its position is.

    Parameters
    ----------
    number : int
        Position of Odb object in session Odbs list.
    show_all : bool, optional
        If True, print name of all opened Odbs.

    Returns
    -------
    str
        Name of opened Odb object from current session.
    """
    # Get list of opened Odbs keys, sort it and select one by position.
    keys = session.odbs.keys()
    keys = sorted(keys)
    selected_key = keys[number]

    # Print list of opened Odbs.
    if show_all:
        print('Currently opened Odbs', keys)
    return selected_key


def retrieve_odb_set_name(odb, number, show_all=False):
    """Get set name from a Odb object, depending on its position.

    This function orders Odb sets list alphabetically, and retrieves
    the name of a set object, depending on its position in that list.
    Useful when set name is not known, but its position is.

    Parameters
    ----------
    odb : Odb object or string.like Path
        Odb object identifier.
    number : int
        Position of set object in Odb sets list.
    show_all : bool, optional
        If True, print name of all Odb sets name.

    Returns
    -------
    str
        Name of set name in a Odb object from current session.
    """
    # Get list of Odb sets keys, sort it and select one by position.
    odb = normalize_odb_object(odb)
    keys = odb.rootAssembly.nodeSets.keys()
    keys = sorted(keys)
    selected_key = keys[number]

    # Print list of available node sets.
    if show_all:
        print('Available node sets', keys)
    return selected_key


def upgrade_odbs_folder(odbs_folder, recursive=False, print_every=1):
    """Upgrade version of all Odb objects in a folder.

    Parameters
    ----------
    odbs_folder : Path
        Folder containing Odb objects.
    recursive : bool, optional
        If True, list Odb files recursively, including subfolders.
    print_every : int, optional
        If given, reduces printing reports frequency.

    Returns
    -------
    None
    """
    # List Odb paths, filter only old versioned and report.
    odb_list = ft.list_files_with_extension(odbs_folder, '.odb', 1, recursive)
    upgradable_odb_list = [i for i in
                           odb_list if odbAccess.isUpgradeRequiredForOdb(i)]
    print(len(odb_list), 'Odb objects found', len(upgradable_odb_list),
          'require upgrade')

    # Set temporary names and iterate over old versioned Odbs.
    temp_name = os.path.join(odbs_folder, 'temp_odb_name.odb')
    for job_number, job_key in enumerate(upgradable_odb_list):

        # Optionally, report less times.
        if divmod(job_number, print_every)[1] == 0:
            print('Processing', job_key,
                  job_number + 1, 'of', len(upgradable_odb_list))

        # Upgrade and rename new and old Odb files.
        new_name = job_key
        old_name = job_key.replace('.odb', '-old.odb')
        session.upgradeOdb(job_key, temp_name)
        os.rename(job_key, old_name)
        os.rename(temp_name, new_name)
    print('DONE')
    return

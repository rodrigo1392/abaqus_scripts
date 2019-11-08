""" Functions to be used by the Abaqus CAE Python interpreter.
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from caeModules import *
from collections import OrderedDict
import collections
import os
from tools_submodule.filesystem_tools import files_with_extension_lister


def mesh_extract_set_nodes(i_set_name, i_odb):
    """
    Returns a dict with a list of mesh nodes labels for all the set_name points as values,
    and the instance names as keys.
    Inputs: set_name = str. Name of set which points labels are to be extracted.
            odb = Odb object to read from.
    Output: Dict with nodes labels of the input set.
    """
    print('Extracting nodes...')
    node_set = i_odb.rootAssembly.nodeSets[i_set_name]
    instances_names_list = [i for i in node_set.instanceNames]
    # nodes = i_odb.rootAssembly.nodeSets[i_set_name].nodes[0]
    output = {i_set_name:
              {instance_name:
               collections.OrderedDict((node.label, node.coordinates) for
                                       node in node_set.nodes[num])
               for num, instance_name in enumerate(instances_names_list)}}
    return output


def models_modify_set_name(set_name, new_set_name):
    """
    Modifies the name of a set in all the Models of the current Database.
    Inputs: set_name = string. Name of the set to be renamed.
            new_set_name = string. New name for the set.
    """
    for model_key, model in mdb.models.items():
        model.rootAssembly.sets.changeKey(fromName=set_name, toName=new_set_name)
    return


def odbs_show_calc_time_folder(odbs_folder):
    """
    Prints the calculation time for the all the odbs of the odbs_folder. """
    for job_key in files_with_extension_lister(odbs_folder, 'odb'):
        try:
            ODB = session.openOdb(odbs_folder + job_key + '.odb', readOnly=True)
            calc_time = ODB.diagnosticData.jobTime
            print(job_key, ': ', str(calc_time))
            ODB.close()
        except:
            print(job_key + ': not found')
            pass
    return calc_time


def odbs_show_calc_time(i_odb):
    """ Shows the calculation time for the i_odb.
    i_odb = Odb. To read the calculation data from. """
    calc_time = i_odb.diagnosticData.jobTime
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    print(odb_name, ': ', str(calc_time))
    return calc_time


def reports_create_fbody(i_first_chars, i_folder_reports, i_odb, i_step_number,
                         i_frame_number, i_surfaces_list):
    """ Creates an Abaqus Freebody Report file with the freebodycut
        created during the process.
        i_first_chars = srt. First chars to add to the report name.
        i_folder_reports = srt. Path to save the Report to
        i_odb = Odb. File to read from.
        i_step_number = int. Step number to read from.
        i_frame_number = int. Frame number to read from.
        i_surfaces_list = List. Surface to make the body cut from. """
    # Show ODB
    session.viewports['Viewport: 1'].setValues(displayedObject=i_odb)
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    # Create bodycut
    leaf = dgo.LeafFromSurfaceSets(surfaceSets=i_surfaces_list)
    session.FreeBodyFromFaces(name='FreeBody-1', faces=leaf,
                              summationLoc=SPECIFY,
                              summationPoint=(0.0, 0.0, 0.0),
                              componentResolution=NORMAL_TANGENTIAL)
    session.viewports['Viewport: 1'].odbDisplay.setValues\
        (freeBodyNames=('FreeBody-1', ), freeBody=ON)
    # Create the report file
    report_name = ''.join([i_folder_reports, i_first_chars, odb_name, '.rpt'])
    session.writeFreeBodyReport(fileName=report_name, append=OFF,
                                step=i_step_number, frame=i_frame_number,
                                stepFrame=ALL, odb=i_odb)
    return report_name, odb_name


def reports_create_field(i_first_chars, i_folder_reports, i_odb, i_step_number,
                         i_frame_number, i_output_position, i_variable):
    """ Creates an Abaqus Field Report file for the RF variable.
        i_first_chars = srt. First chars to add to the report name.
        i_folder_reports = srt. Path to save the Report to
        i_odb = Odb. File to read from.
        i_step_number = int. Step number to read from.
        i_frame_number = int. Frame number to read from.
        i_ouput_position = Abaqus keyword.
        i_variable = Abaqus keyword"""
    # Show ODB
    session.viewports['Viewport: 1'].setValues(displayedObject=i_odb)
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    # Create the report file
    report_name = ''.join([i_folder_reports, i_first_chars, odb_name, '.rpt'])
    session.writeFieldReport(fileName=report_name, append=OFF,
                             sortItem='Node Label', odb=i_odb,
                             step=i_step_number, frame=i_frame_number,
                             outputPosition=i_output_position,
                             variable=i_variable)
    return report_name


def reports_create_xydata(i_first_chars, i_xydata_list, i_folder_reports,
                          i_odb):
    """ Creates an Abaqus XY Report file with the xyData corresponding
        to the list given by i_xydata_list.
        i_first_chars = srt. First chars to add to the report name.
        i_xydata_list = list of srt. Names of the xyData objects.
        i_folder_reports = srt. Path to save the Report to .
        i_odb = Odb. File to read from. """
    print('Creating XYdata Report...')
    # Show ODB
    session.viewports['Viewport: 1'].setValues(displayedObject=i_odb)
    session.xyReportOptions.setValues(totals=ON, minMax=ON)
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    # Extract the xyData
    xy_objects = {}
    for xydata_name in i_xydata_list:
        # Copies the xyData with a much more simplier name,
        # in order to make the Report file more readable
        dash_pos = [pos for pos, char in enumerate(xydata_name) if char == '-']
        new_xydata_name = xydata_name[(dash_pos[(len(dash_pos) - 1)] + 1):]
        if len(new_xydata_name) > 17:
            dash_pos = [pos for pos, char in enumerate(new_xydata_name) if char == '_']
            to_delete = new_xydata_name[dash_pos[0] + 2: dash_pos[-1] - 1]
            new_xydata_name = new_xydata_name.replace(to_delete, '')
        # If it already exists it has to be eliminated in order to
        # place the new one
        if new_xydata_name in session.xyDataObjects.keys():
            del session.xyDataObjects[new_xydata_name]
        session.XYData(name=new_xydata_name,
                       objectToCopy=session.xyDataObjects[xydata_name])
        xy_objects[new_xydata_name] = session.xyDataObjects[new_xydata_name]
    xy_objects = collections.OrderedDict(sorted(xy_objects.items()))
    # Create the report file
    report_name = ''.join([i_folder_reports, i_first_chars, odb_name, '.rpt'])
    session.writeXYReport(fileName=report_name, appendMode=OFF,
                          xyData=xy_objects.values())
    return report_name


def xydata_create_t_history_point(i_odb, i_set_dict, i_steps_names_list,
                                  i_variables_list):
    """ Creates a xydata from the values for the point of interest.
        i_odb =  OdbObject. Odb to read from.
        i_set_dict = dict. Labels to extract for.
        i_steps_names_list = list of str. Steps a to read in.
        i_variables_list = listof str. Variables to be extracted."""
    var_description_dict = {'Spatial acceleration': ['A1', 'A2', 'A3'],
                            'Spatial displacement': ['U1', 'U2', 'U3'],
                            'Spatial velocity': ['V1', 'V2', 'V3'],
                            'Pore or Acoustic Pressure': ['POR'],
                            'Reaction force': ['RF1', 'RF2', 'RF3'],
                            'Total force on the surface': ['SOF1', 'SOF2',
                                                           'SOF3'],
                            'Total moment on the surface': ['SOM1', 'SOM2',
                                                            'SOM3']}
    print('Creating History XYdata for a Point...')
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    instances = i_odb.rootAssembly.instances
    #points_meta = {k:v.description for k,v in step.historyRegions[].historyOutputs}
    xydata_names_list = []
    set_name = i_set_dict.keys()[0]
    for instance_name, labels_dict in i_set_dict[set_name].items():
        for variable in i_variables_list:
            for label in labels_dict.keys():
                xydata_name = ''.join([odb_name, '-P', str(label), '_',
                                       set_name, '_', variable])
                xydata_names_list.append(xydata_name)
                for k, v in var_description_dict.items():
                    if variable in v:
                        var_description = k
                if len(instances) > 1:
                    session.\
                     XYDataFromHistory(name=xydata_name, odb=i_odb,
                                       outputVariableName=''.join([var_description, ': ',
                                                                   variable, ' PI: ', instance_name, ' Node ',
                                                                   str(label), ' in NSET ',
                                                                   set_name]),
                                       steps=i_steps_names_list,
                                       __linkedVpName__='Viewport: 1')
                else:
                    session.\
                     XYDataFromHistory(name=xydata_name, odb=i_odb,
                                       outputVariableName=''.join([var_description, ': ',
                                                                   variable, ' at Node ',
                                                                   str(label), ' in NSET ',
                                                                   set_name]),
                                       steps=i_steps_names_list,
                                       __linkedVpName__='Viewport: 1')
    return xydata_names_list


def xydata_create_t_history_sum(i_odb, i_set_dict, i_steps_names_list,
                                i_variables_list):
    """ Creates a xydata from the Sum of the i_variable value of each
        point in the i_set_dict against time, for all the steps contained
        in i_steps_names_list.
        i_odb = OdbObject. Odb to read from.
        i_set_dict = dict. Labels to extract for.
        i_steps_names_list = list of str. Steps a to read in.
        i_variable = str. Variable to be Summed. """
    print('Creating History Sum XYdata for a Set...')
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    var_description_dict = {'Spatial acceleration': ['A1', 'A2', 'A3'],
                            'Spatial displacement': ['U1', 'U2', 'U3'],
                            'Spatial velocity': ['V1', 'V2', 'V3'],
                            'Pore or Acoustic Pressure': ['POR'],
                            'Reaction force': ['RF1', 'RF2', 'RF3'],
                            'Total force on the surface': ['SOF1', 'SOF2',
                                                           'SOF3'],
                            'Total moment on the surface':['SOM1', 'SOM2',
                                                           'SOM3']}
    # Create variables in loop with the results of each point
    instances = i_odb.rootAssembly.instances
    xydata_names_list = []
    set_name = i_set_dict.keys()[0]
    for instance_name, labels_set in i_set_dict[set_name].items():
        for variable in i_variables_list:
            xydata_name = ''.join([odb_name, '-', set_name, '_', variable])
            xydata_names_list.append(xydata_name)
            for k, v in var_description_dict.items():
                if variable in v:
                    var_description = k
            if len(instances) > 1:
                suma = sum([xyPlot.XYDataFromHistory(odb=i_odb,\
                                outputVariableName=''.join([var_description, ': ',
                                                                variable, ' PI: ', instance_name, ' Node ',
                                                                str(label), ' in NSET ',
                                                                set_name]),
                            steps=i_steps_names_list, suppressQuery=True,
                            __linkedVpName__='Viewport: 1') for label in labels_set])
            else:
                suma = sum([xyPlot.XYDataFromHistory(odb=i_odb,\
                                outputVariableName=''.join([var_description, ': ', variable,
                                                    ' at Node ', str(label), ' in NSET ',
                                                    set_name]),
                            steps=i_steps_names_list, suppressQuery=True,
                            __linkedVpName__='Viewport: 1') for label in labels_set])
            session.XYData(name=xydata_name, objectToCopy=suma)
    # Clean temporal data
    for xydata_key in session.xyDataObjects.keys():
        if xydata_key[0:5] == '_temp':
            if xydata_key != xydata_name:
                del session.xyDataObjects[xydata_key]
    return xydata_names_list


def xydata_create_t_history_section(i_odb, i_section_name, i_set_name,
                                    i_steps_names_list, i_var_description,
                                    i_variable):
    """ Creates a xydata from the values for the point of interest.
        i_odb =  OdbObject. Odb to read from.
        i_set_name = srt. Name of the Surface Set.
        i_section_name = srt. Name of the Integrated Section.
        i_steps_names_list = list of str. Steps a to read in.
        i_var_description= str. Abaqus variable for constructing
                                the extraction op.
        i_variable = str. Variable to be Summed
        Possible description and its variables:
        'Total force on the surface' - SOF1, SOF2, SOF3, SOFM.
        'Total moment on the surface' - SOM1, SOM2, SOM3, SOMM.  """
    print('Creating History XYdata for a Integrated Section...')
    odb_name = (os.path.splitext(os.path.basename(i_odb.name))[0])
    xydata_name = ''.join([odb_name, '_', i_set_name, '-', i_section_name, '_',
                          i_variable])
    session.XYDataFromHistory\
        (name=xydata_name, odb=i_odb,
         outputVariableName=''.join([i_var_description, ': ', i_variable,
                                     '  on section ', i_section_name,
                                     ' in SSET ', i_set_name]),
         steps=i_steps_names_list, __linkedVpName__='Viewport: 1')
    # Change the sign of the result
    f_xy1 = session.xyDataObjects[xydata_name] * -1
    del session.xyDataObjects[xydata_name]
    session.xyDataObjects.changeKey(f_xy1.name, xydata_name)
    return xydata_name

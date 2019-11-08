""" Functions related to Abaqus, to be used by an external Python interpreter.
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from caeModules import *
from collections import OrderedDict
import collections
import os


def abaqus_process(list_scripts_folder, script_name, options_input, show_process_option):
    """ Runs an script in an Abaqus cae instance.
        list_scripts_folder = Path.
        script_name = str. Script name to be run.
        options_input = dict. Paths and Files names to be passed to the script
        show_process_option = Boolean. If True, shows the CAE window. """
    import subprocess
    with open(PATH_TEMP, 'wb') as fileobject:
        pickle.dump(options_input, fileobject)
    # ******************** Launch abaqus subprocess *******************
    clock_start = clock()
    os.chdir(list_scripts_folder)
    if show_process_option is True:
        proc_state = subprocess.call('abaqus cae -script ' + script_name,
                                     shell=True)
    else:
        proc_state = subprocess.call('abaqus cae noGUI=' + script_name,
                                     shell=True)
    if proc_state == 0:
        print ('Process well runned')
    print('Abaqus time elapsed: ',
          str(round(clock() - clock_start, 2)), ' s')
    # *****************************************************************
    return proc_state


def abaqus_process_2(list_scripts_folder, script_name, options_input, show_process_option):
    PATH_TEMP = options_input['PATH_TEMP']
    import subprocess
    with open(PATH_TEMP, 'wb') as fileobject:
        pickle.dump(options_input, fileobject)
    # ******************** Launch abaqus subprocess *******************
    clock_start = clock()
    os.chdir(list_scripts_folder)
    if show_process_option is True:
        process = subprocess.Popen('abaqus cae -script ' + script_name,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True)
        process.wait()
        out, err = process.communicate()
    else:
        process = subprocess.Popen('abaqus cae noGUI=' + script_name,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True)
        process.wait()
        out, err = process.communicate()
    print(out)
    print(err)
    if process == 0:
        print ('Process well runned')
    print('Abaqus time elapsed: ',
          str(round(clock() - clock_start, 2)), ' s')
    # *****************************************************************
    return process


def abaqus_process3(i_script, show_process_option, args = []):
    """ Runs an script in an Abaqus cae instance.
        list_scripts_folder = Path.
        script_name = str. Script name to be run.
        options_input = dict. Paths and Files names to be passed to the script
        show_process_option = Boolean. If True, shows the CAE window. """
    import subprocess, os
    os.chdir(SCPRITS_FOLDER)
    # ******************** Launch abaqus subprocess *******************
    clock_start = clock()
    args = ' '.join(args)
    if show_process_option is True:
        proc_state = subprocess.call('abaqus cae -script ' + i_script + ' -- ' + args,
                                     shell=True)
        print('abaqus cae -script ' + i_script + ' ' + args)
    else:
        proc_state = subprocess.call('abaqus cae noGUI=' + i_script + ' -- ' + args,
                                     shell=True)
    if proc_state == 0:
        print ('Process well runned')
    print('Abaqus time elapsed: ',
          str(round(clock() - clock_start, 2)), ' s')
    # *****************************************************************
    return proc_state


def abaqus_parametric_fea_check_files(root_path):
    """
    Checks for availability of sequentially numbered Abaqus output files, using the .log files
    of each job run.
    Input: root_path. Path to investigate.
    Output: Boolean. True if no file is missing and if all .log files statuses are 'COMPLETED'.
            False otherwise.
    """
    root_path = str(root_path)
    strings_list = files_with_extension_lister(root_path, 'log', True, False)
    numbers = [int(re.findall(r'-?\d+\.?\d*', i)[-1].replace('.', '')) for i in strings_list]
    status_out = True
    check_files, missing_files = math_tools.array_1d_consecutiveness_check(numbers)
    if not check_files:
        print('WARNING: MODELS', missing_files, 'MISSING')
        print('CURRENT NUMBERS: ', numbers)
        status_out = False
    for i in strings_list:
        with open(i) as file_read:
            lines_list = file_read.readlines()
            status = lines_list[-1].split(' ')[-1]
        if status != 'COMPLETED\n':
            print('WARNING: JOB ', i, ' NOT COMPLETED')
            status_out = False
    print('Parametric files in ' + root_path + ' in good condition:', status_out)
    return status_out

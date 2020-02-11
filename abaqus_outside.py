""" Functions related to Abaqus, to be used by an external Python interpreter.
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""

import ast
import configparser
import io
import multiprocessing
import numpy as np
import os
import pandas as pd
import pprint
import subprocess
import shutil
from tools_submodule import databases_tools as db
from tools_submodule import filesystem_tools as ft
from tools_submodule import strings_tools as st
from tools_submodule import math_tools as mt
from pathlib import Path


def parametric_create_files(config_file):
    """
    Generate files necessary for parametric analysis within abaqus.
    Input: config_file. Path of config file for the study.
    """

    def parametric_csv_builder(study_nam, parameters_list, max_values, min_values, normal_values,
                               sample_size=10, analysis_folder=None, overwrite_csv=False,
                               study_folde=None, **kwargs):
        """
        Creates a csv file with values of input parameters for an Abaqus parametric analysis.
        Inputs: study_nam. Name of the parametric analysis project.
                parameters_list. List of parameters for the study.
                max_values. List of maximum values of each parameter.
                min_values. List of minimum values of each parameter.
                normal_values. List of reference values of each parameter.
                sample_size. Size of sampling vector when studying only one parameter.
                analysis_folder. Path of folder to copy the output to.
                overwrite_csv. Boolean, if True, allows for output overwriting.
                study_folde. Path to copy the output to. If not provided, the script assumes
                              ./study_nam to be the output folder.
        """
        if not study_folde:                                                      # Set default study folder
            study_folde = Path.cwd() / study_name
        output_csv = (study_folde / study_nam).with_suffix('.csv')               # Set output folder
        if len(parameters_list) == 1:                                            # Sample without doe for one parameter
            samples = np.linspace(min_values[0], max_values[0], sample_size)     # Sample with uniform vector
            samples = sorted(list(samples) + normal_values)                      # Add characteristic value to sample
            df = pd.DataFrame(samples, columns=parameters_list)                  # Build pandas data-frame
        df.insert(0, "MODEL_NO", range(1, df.shape[0] + 1), True)                # Insert 'Models' number column
        db.dataframe_safe_save(df, output_csv, overwrite_csv)                    # Save csv file in study folder
        if analysis_folder:                                                      # If analysis folder, copy csv to it:
            analysis_folder = Path(analysis_folder, study_nam)                   # set analysis folder
            ft.folder_create_if_not(analysis_folder)                             # create output folder if not present
            shutil.copy(output_csv, analysis_folder / output_csv.name)           # copy output to it
        return output_csv

    def parametric_psf_builder(parameter_values_file, parameters_list, inp_file_name,
                               analysis_folder=None, **kwargs):
        """
        Create *.psf file, for parametric analysis from abaqus command line.
        Input: parameter_values_file. Csv file containing input variables values.
               parameters_list. List of parameters for the study.
               inp_file_name. Name of the inp file which defines the FEA model. Abaqus expects it to
                              be on the same folder than the psf file when running it.
               analysis_folder. Path to copy the output file to.
        Output: Path of psf file.
        """
        study_nam = Path(parameter_values_file).stem                             # Extract study name
        inp_file_name = Path(inp_file_name).name                                 # Set inp file name
        output_psf_path = Path(parameter_values_file).with_suffix('.psf')        # Set output psf file
        change_folder_line = ''
        if analysis_folder:                                                      # If analysis folder, chdir to it
            ft.folder_create_if_not(Path(analysis_folder, study_nam))            # create output folder if necessary
            change_folder_line = 'os.chdir("' + analysis_folder + '/'\
                                 + study_nam + '/' + '")'
        header = ['import csv', 'import os',                                     # Header of psf script
                  'print("EXECUTION FOLDER: " + os.getcwd())',                   # Lines for changing dir
                  change_folder_line,
                  'with open("' + study_nam + '.csv") as csvfile:',              # Lines to extract pars from csv
                  '    reader = csv.DictReader(csvfile)',
                  '    lines = [row for row in reader]',
                  'parameters = ' + str(parameters_list),
                  'domains = {parameter :'
                  '[k[parameter] for k in lines] for parameter in parameters}']
        study_lines = ['study = ParStudy(par=(parameters))',                     # Create study
                       'for parameter in parameters:',                           # Define parameters
                       '    study.define(DISCRETE,'
                       'par=parameter, domain=domains[parameter])',
                       'for parameter in parameters:',                           # Sample from csv file
                       '    study.sample(INTERVAL, interval=1, par=parameter)',
                       'study.combine(TUPLE, name=' + '"model")',                # Combine samples with tuple method
                       'study.generate(template="' + inp_file_name + '")']       # Generate jobs
        with open(output_psf_path, 'w') as file:                                 # Save output psf file
            file.write('\n'.join(header + study_lines))
            print('*** PSF file created ***')
        return output_psf_path

    def parametric_modify_inp(inp_file_name, parameters_list,
                              analysis_folder=None, study_folde=None, **kwargs):
        """
        Modify inp file, to include parameters information. Inp file is expected to be found either
        on the study folder or the analysis_folder.
        Input: inp_filename. Name of the Inp file to be modified.
               parameters_list. List of parameters for the study.
               analysis_folder. Path of folder to copy the output inp file to.
               study_folde. Path of the folder to read the inp file from.
        Output: Path of inp file.
        """
        inp_variables_names = {'ALPHA_DYN': 'Dynamic,alpha', 'E': 'Elastic'}     # Parameters Keywords in inp file
        inp_name = Path(inp_file_name).with_suffix('.inp')                       # Normalize inp file suffix
        study_nam = inp_name.stem                                                # Extract study name
        if not study_folde:                                                      # Set default study folder
            study_folde = Path(Path.cwd() / study_nam)
        inp_path = Path(study_folde, inp_name)                                   # Search inp in study folder
        if inp_path.exists():
            pass
        else:                                                                    # If inp not in study folder,
            inp_path_analysis = Path(analysis_folder, inp_name)                  # search inp from analysis folder
            shutil.copy(inp_path_analysis, inp_path)                             # copy it to to study folder
        inp_path = ft.file_save_with_old_version(inp_path)                       # Save old version before modifying
        with open(inp_path, 'r+') as file:                                       # Load inp file
            lines = file.readlines()
        par_lines = [str(par) + '=100\n' for par in parameters_list]             # Initialize parameters
        assembly_line = [(n, i) for n, i in enumerate(lines)
                         if '** ASSEMBLY' in i][0][0]
        lines[assembly_line:assembly_line] = ['* PARAMETER\n'] + par_lines       # Insert initialization lines
        for par in parameters_list:                                              # Insert modified lines
            for n, line in enumerate(lines):
                key = inp_variables_names[par]
                if key in line:
                    after_key = line.partition(key)[-1]
                    if after_key[0] == '=':
                        lines[n] = line.replace(after_key.partition(',')[0],
                                                '=<' + par + '>')
                    else:
                        value = lines[n + 1].partition(key)[-1].partition(',')[0]
                        lines[n + 1] = lines[n + 1].replace(value, '<' + parameter + '>')
        out_inp_file = inp_path                                                  # Set output inp path
        with open(out_inp_file, 'w+') as file:                                   # Save inp file
            file.write(''.join(lines))
        if analysis_folder:                                                      # Copy output file to analysis folder
            copy_path = Path(analysis_folder, study_nam, out_inp_file.name)
            shutil.copy(out_inp_file, copy_path)
        print('*** INP file modified ***')
        return out_inp_file

    def modify_psf_4_run(psf_fil, analysis_folder=None, cpu_numbers=8, **kwargs):
        """
        Modifies psf file, leaving only the lines necessary to run the parametric jobs,
        and adds a line to execute them.
        Inputs: psu_file. Psu file to be modified.
                analysis_folder. Path to copy the output to.
                cpu_numbers. Int of amount of cpu to be used in the analysis.
        Output: Path of the modified psf file.
        """
        study_nam = Path(psf_fil).stem                                           # Extract study name
        output_psf = psf_fil                                                     # Set default output psf path
        if analysis_folder:                                                      # Set analysis folder output psf
            output_psf = Path(analysis_folder,
                              study_nam, study_nam).with_suffix('.psf')
        with open(psf_fil) as input_psf:                                         # Read input psf
            lines = input_psf.readlines()
        line_0 = []                                                              # Extract lines of interest
        if analysis_folder:                                                      # Line to chdir to analysis folder
            line_0 = [[i for i in lines if 'os.chdir' in i][0]]
        parameters_line = [[i for i in lines if 'parameters = ' in i][0]]        # Line with parameters list
        study_line = [[i for i in lines if 'study = ' in i][0]]                  # Line with study details
        execution_line = ['study.execute(ALL, execOptions = ' +                  # Execution line
                          '"cpus=' + str(cpu_numbers) + '")']
        with open(output_psf, 'w+') as output_file:                              # Write output file
            output_file.write(''.join(line_0 + parameters_line
                                      + study_line + execution_line))
        return output_psf

    input_data = ft.config_file_extract_input(config_file)                       # Extract input data
    study_name = config_file.stem                                                # Extract study name
    study_folder = ft.folder_create_if_not(Path.cwd() / study_name)              # Set project sub-folder
    input_data['study_name'], = study_name                                       # Pass study name and folder to kwags
    input_data['study_folder'] = study_folder
    max_cpu_no = multiprocessing.cpu_count()                                     # Check maximum cpu numbers
    if 'cpu_numbers' not in input_data or int(input_data['cpu_numbers']) > max_cpu_no:
        input_data['cpu_numbers'] = max_cpu_no
    if 'inp_file_name' not in input_data:                                        # Set default input file path
        input_data['inp_file_name'] = study_name
    if 'analysis_folder' not in input_data:                                      # Set default analysis folder
        input_data['analysis_folder'] = study_folder
    csv_file = parametric_csv_builder(study_nam=input_data['study_name'],        # Create csv input file
                                      **input_data)
    psf_file = parametric_psf_builder(parameter_values_file=csv_file,            # Create psf script
                                      **input_data)
    parametric_modify_inp(**input_data)                                          # Modify inp file
    run_psf(psf_file, **input_data)                                              # Run psf and get inp files
    return modify_psf_4_run(psf_file, **input_data)                              # Modify psf file for FEA


def parametric_check_odb_files(root_path):
    """
    Checks for availability of sequentially numbered Abaqus output files, using the .log files
    of each job run.
    Input: root_path. Path to investigate.
    Output: Boolean. True if no file is missing and if all .log files statuses are 'COMPLETED'.
            False otherwise.
    """
    strings_list = files_with_extension_lister(root_path, 'log', True, False)    # List log files in root_path
    numbers = [st.str_extract_last_int(i) for i in
               st.sort_strings_by_digit(strings_list)]                           # Extract numbers from log files
    status_out = True
    check_files, missing_files = mt.array_1d_consecutiveness_check(numbers)      # Check log files consecutiveness
    if not check_files:                                                          # Report missing files
        print('WARNING: MODELS', missing_files, 'MISSING')
        print('CURRENT NUMBERS: ', numbers)
        status_out = False
    for i in strings_list:                                                       # Report jobs status
        with open(i) as file_read:
            lines_list = file_read.readlines()
            status = lines_list[-1].split(' ')[-1]
        if status != 'COMPLETED\n':
            print('WARNING: JOB ', i, ' NOT COMPLETED')
            status_out = False
    print('Parametric files in ' + root_path + ' in good condition:',            # Report general status
          status_out)
    return status_out


def parametric_extract_fea_data(config_file):
    """
    Gathers output data from Abaqus odb files, calling a post-process script within an
    Abaqus subprocess in batch.
    Input: config_file. Project config file with options and paths specified in inner functions.
    Output: List of output variable references.
    """
    def parametric_gather_script_modify(extraction_algorithm, database_folder=None,
                                        one_odb_only=False, **kwargs):
        """
        Modifiy post-process Abaqus script, to allow for batch processing and gathering of output from
        subprocess to main process. Any file generated by Abaqus, is to be stored in a 'temp_files'
        subfolder in the extraction algorithm folder.
        Inputs: extraction_algoritm. Path of post-process python script.
                database_folder. Path of folder with odb files.
                one_odb_only. Boolean, if True, run post-process script only for one odb in the folder.
                              Use it for debugging.
        Output: Path of temp modified script.
        """
        study_folde = extraction_algorithm.parent                                # Set study sub-folder
        with open(extraction_algorithm, 'r+') as script:                         # Read extraction script
            algo_lines = script.readlines()
        time_history, th = False, []                                             # Initialize time history vars as False
        closer = []                                                              # Initialize batch closer line as empty
        for line in algo_lines:                                                  # Check if there is time history data
            if 'XYDataFromHistory' in line:
                time_history = True
                break
        header = ['import os', 'import sys',                                     # Lines of header
                  'os.chdir(sys.argv[-1])',                                      # Lines for chdir to current workflow
                  'import csv', 'import numpy as np',
                  'from abaqus_scripts.abaqus_inside import *']
        if database_folder:                                                      # Lines of odb files batch
            odb_list = ft.files_with_extension_lister(database_folder,
                                                      '.odb')
            odb_list = [str(t) for t in odb_list]
            if one_odb_only:                                                     # Pass only one odb is option if True
                odb_list = odb_list[0:1]
            odb_header = ['odb_list=' + repr(odb_list),                          # Lines for loading odb paths
                          'for odb_path in odb_list:',
                          '    odb = session.openOdb(odb_path)']
            closer = ['    odb.close()']
            algo_lines = odb_header + ['    ' + x for x in algo_lines]           # Indent body of script for batch
        if time_history:                                                         # Lines for time history data extract
            parent_dir, npz_name = '', 'odb_name.replace(".odb",".npz")'         # Set names of npz files
            th = ['data = {k: v for k, v in session.xyDataObjects.items()}',
                  'odb_name = odbs_retrieve_name(0)',
                  'npz_name = ' +
                  repr(str(study_folde / 'temp_files') + '/') +
                  ' + ' + npz_name + ".split('/')[-1]",
                  'np.savez(npz_name, **data)',                                  # Line for saving npz files
                  'log_abaqus("npz saved:")',                                    # Line for logging variables references
                  'log_abaqus(npz_name)']
            if database_folder:
                th = ['    ' + x for x in th]                                    # Indent time history lines for batch
        lines_to_exec = '\n'.join(header + algo_lines + th + closer)             # Assembly modified script lines
        temp_folder = ft.folder_create_if_not(study_folder / 'temp_files')       # Create temp folder if does not exist
        modified_script_path = Path(temp_folder,                                 # Set temp script path
                                    'temp_script').with_suffix('.py')
        with open(modified_script_path, 'w+') as out_file:                       # Save temp script
            out_file.write(lines_to_exec)
        print('*** GATHER SCRIPT MODIFIED ***')
        return modified_script_path

    input_cfg = ft.config_file_extract_input(config_file)                        # Read input config
    study_name = config_file.stem                                                # Get study name
    study_folder = Path(Path.cwd() / study_name)                                 # Set study subfolder
    input_cfg['study_folde'] = study_folder                                      # Build kwags cfg dict
    if not input_cfg['extraction_algorithm']:                                    # Set default cfg values
        input_cfg['extraction_algorithm'] = Path(study_folder,
                                                 study_name).with_suffix('.py')
    if not input_cfg['database_folder']:
        input_cfg['database_folder'] = Path(input_cfg['database_folder'], study_name)
    default_false_vars = ['gui', 'verbose', 'one_odb_only']
    for i in default_false_vars:
        if i not in input_cfg.keys():
            input_cfg[i] = False
    modified_script = parametric_gather_script_modify(**input_cfg)               # Modify gather script for batch
    output_vars = run_abaqus_subprocess(script=modified_script, **input_cfg)     # Run it
    return output_vars


def parametric_summarize_output(config_file):
    """
    Loads output npz files generated by Abaqus and save them in a unique hdf5 file,
    corresponding to the project in course.
    Input: config_file. Cfg file containing details of Abaqus study.
    Output: Path of hdf5 file.
    """
    study_name = Path(config_file).stem                                          # Get study name
    temp_folder = Path(Path.cwd() / study_name / 'temp_files')                   # Set input files folder
    csv_file = Path(config_file).with_suffix('.csv')                             # Set csv input file
    hdf_path = Path(config_file).with_suffix('.hdf5')                            # Set output hdf5 file
    df = pd.read_csv(csv_file)                                                   # Extract parametric data from csv
    df.set_index('MODEL_NO', inplace=True)                                       # Set model names as data-frame index
    df_dict = df.to_dict(orient='index')                                         # Convert data-frame to dict
    npz_files_paths = ft.files_with_extension_lister(temp_folder, '.npz')        # List npz files
    npz_files_nos = [st.str_extract_last_int(i.stem) for i in npz_files_paths]   # Try to get models numbers
    npz_attributes = [df_dict[i].items() for i in npz_files_nos]                 # Extract attributes from data-frame
    input_config = ft.config_file_extract_input(config_file)                     # Input config for printing or not
    db.npz_to_hdf5(npz_files_list=npz_files_paths, hdf5_path=hdf_path,           # Save npz to hdf5 file
                   attributes_dict=npz_attributes,
                   print_structure=input_config['print_hdf5'])
    hdf_path_tr = Path(hdf_path.parent, 'temp_files', hdf_path.name)             # Swap groups and subgroups
    db.hdf5_swap_groups_and_subgroups(hdf_path, hd_out=hdf_path_tr)
    shutil.copy(hdf_path_tr, hdf_path)                                           # Copy from temporary swapped file
    print('*** HDF5 file created ***')
    return hdf_path


def run_abaqus_subprocess(script, gui=False, database_folder=None, verbose=False, **kwargs):
    """
    Run script in a Abaqus cae subprocess and gather the data printed inside Abaqus python environment.
    Inputs: script. PAth of script to be runned.
            gui. Boolean, if True, open GUI version of CAE.
            database_folder. Path of folder to change dir to.
            verbose. Boolean, if True, print output variable references.
    Output: List of output variable references generated by script.
    """
    print('*** RUNNING ' + script.name + ' ***')
    script = str(script)                                                         # Normalize script path to string
    if gui:                                                                      # Select Abaqus start command for cmd
        command = 'abaqus cae script='
    else:
        command = 'abaqus cae noGUI='
    process = command + script                                                   # Set command line for cmd
    if database_folder:                                                          # Modify it if database folder
        process = r'SET original_folder=%cd% & cd ' + database_folder +\
                  ' & ECHO %cd% & cd & ' + command + script + ' -- %cd%'         # Include chdir actions
    p = subprocess.Popen(process, shell=True, stdout=subprocess.PIPE)            # Launch subprocess
    out, err = p.communicate()                                                   # Wait completion
    print('*** DONE EXECUTING ABAQUS SUBPROCESS ***')                            # Report completion
    print('ERROR:', err)                                                         # Report errors
    out_var_references = [i.decode("utf-8") for i in out.split(b'\r\n')]         # Get Abaqus messages
    if verbose:                                                                  # If verbose, print them
        pprint.pprint(out_var_references)
    paths_to_strip = [Path.cwd()]                                                # Filter output variable references
    if database_folder:
        paths_to_strip.append(Path(database_folder))
    out_var_references = [i for i in out_var_references if                       # Strip sys argv and empty spaces
                          Path(i) not in paths_to_strip and ' ' not in i]
    return out_var_references


def run_psf(input_var, **kwargs):
    """
    Runs parametric analysis in a separate cmd subprocess.
    Input: input_var. If it is a psf file, run it with subprocess. If it is a cfg file,
    first figure out path of psf file and then run it.
    """
    if Path(input_var).suffix == '.psf':                                         # If input is a psf file, pass it
        psf_file = str(input_var)
    if Path(input_var).suffix == '.cfg':                                         # If it is a cfg:
        config_data = ft.config_file_extract_input(input_var)                    # read cfg and get analysis folder path
        psf_file = str(Path(config_data['analysis_folder'],
                            input_var.stem, input_var.stem).with_suffix('.psf'))
    print('RUNING', psf_file)
    p = subprocess.Popen('abaqus script=' + psf_file, shell=True)                # Run psf file in no gui environment
    p.communicate()                                                              # Wait for the process to finish

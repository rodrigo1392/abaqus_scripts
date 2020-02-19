"""Functions to manage SIMULIA Abaqus processes externally.

Intended to be used within a Python 3 environment.
Developed by Rodrigo Rivero.
https://github.com/rodrigo1392

"""

import multiprocessing
import numpy as np
import pandas as pd
import pprint
import subprocess
import shutil

from tools_submodule import databases_tools as db
from tools_submodule import filesystem_tools as ft
from tools_submodule import strings_tools as st
from tools_submodule import math_tools as mt
from pathlib import Path


INP_KEYWORDS = {'ALPHA_DYN': 'Dynamic,alpha', 'E': 'Elastic'}


def create_parametric_files(config_file):
    """Generate necessary files for Abaqus parametric analysis.

    The algorithm replaces some of the native Abaqus parametric
    pre-processing mechanisms, in order to automatize some of the slower
    aspects of the workflow. The parameters data (name, range, etc), and
    their combinations, trough DOE sampling, is set in this level.

    Next, this function builds a script file with appropriate commands,
    and runs it through Abaqus command line. Abaqus automatically
    generates a series of models, one inp file with correspondent
    variable values for each of them, and a 'vars' file, containing the
    name of each model and associated parameters values.

    Analysis data, such as list of parameters, their range and reference
    values, folders paths and so on are taken from a configuration file
    named after the parametric study project. In general, most input
    and output files paths can be modified trough this file, but by
    default, is expected to have a sub-folder named after the
    project, with inp and cfg files, and for later use, a gather output
    Abaqus post-process python script.

    In summary, this function performs the following series of steps:
    - Generate samples of parametric variables and save them in a csv.
    - Build psf file with Abaqus commands for creation parametric files.
    - Modify FEA inp file to include parameters information in it.
    - Run psf file trough Abaqus cmd to create models inp files.
    - Modify psf file, leaving it ready to run the parametric jobs.

    Parameters
    ----------
    config_file : Path
        Path of config file containing study data.

    Returns
    -------
    Path
        Psf file for Abaqus cmd to execute simulation jobs.
    """

    def build_parametric_csv(study_nam, parameters_list, max_values,
                             min_values, normal_values, sample_size=10,
                             study_folde=None, analysis_folder=None,
                             overwrite=False, **kwargs):
        """Create csv with samples values for Abaqus parametric study.

        The algorithm calculates samples for each parameter, and saves
        them column-wise, with parameter name as column names. Default
        output folder is a sub-folder named after the study.

        Parameters
        ----------
        study_nam : str
            Name of the parametric analysis project.
        parameters_list : list of str
            Variables to study during parametric analysis.
        max_values, min_values, normal_values : List of float
            Maximum, minimum and reference values of each parameter.
        sample_size : int
            Number of sampling vector for a one parameter study.
        study_folde : Path, optional
            Folder to save the output file to. If not given, the script
            assumes ./study_nam as output folder.
        analysis_folder : Path, optional
            Folder to copy output file to. Default is None.
        overwrite : bool, optional.
            If True, allows output file overwriting.
        **kwargs : dict
            Allows to pass same argument values to different functions.

        Returns
        -------
        Path
            Full path of output csv file.
        """
        # Set default study folder and output csv path.
        if not study_folde:
            study_folde = Path.cwd() / study_name
        output_csv = (study_folde / study_nam).with_suffix('.csv')

        # For one parameter study, sample with uniform vector, add
        # reference value and build pandas data-frame.
        if len(parameters_list) == 1:
            samples = np.linspace(min_values[0], max_values[0], sample_size)
            samples = sorted(list(samples) + normal_values)
            df = pd.DataFrame(samples, columns=parameters_list)

        # Insert 'Models' column as index and save data-frame to csv.
        df.insert(0, "MODEL_NO", range(1, df.shape[0] + 1), True)
        db.save_dataframe_safely(df, output_csv, overwrite)

        # Copy csv to analysis folder, setting local study sub-folder.
        if analysis_folder:
            analysis_folder = Path(analysis_folder, study_nam)
            ft.create_non_existent_folder(analysis_folder)
            shutil.copy(output_csv, analysis_folder / output_csv.name)
        return output_csv

    def build_parametric_psf(parametric_csv, parameters_list,
                             inp_file_name, analysis_folder=None,
                             **kwargs):
        """Create a psf file that defines an Abaqus parametric analysis.

        The algorithm creates a psf text-like file, containing commands
        for Abaqus to create all necessary internal files. Psf files
        must be run in Abaqus command line. It expects that inp and psf
        files be located in the same folder.

        Parameters
        ----------
        parametric_csv : path of csv file
            Contains input variables samples values.
        parameters_list : list of str
            Variables to study during parametric analysis.
        inp_file_name : str
            Name of the inp file that defines the FEA model. Abaqus
            expects it to be on the same folder than the study psf file.
        analysis_folder : Path, optional
            Folder to copy output file to. Default is None.
        **kwargs : dict
            Allows to pass same argument values to different functions.

        Returns
        -------
        Path
            Full path of output psf file.
        """
        # Extract study and inp names, set output psf path.
        study_nam = Path(parametric_csv).stem
        inp_file_name = Path(inp_file_name).name
        output_psf_path = Path(parametric_csv).with_suffix('.psf')

        # Build lines for Abaqus to chdir to analysis folder.
        change_folder_line = ''
        if analysis_folder:
            ft.create_non_existent_folder(Path(analysis_folder, study_nam))
            change_folder_line = 'os.chdir("' + analysis_folder + '/' \
                                 + study_nam + '/' + '")'

        # Build header of psf script file to:
        #
        # Import built-in modules, show execution folder, chdir to
        # analysis folder and extract parameters list and their values
        # from parametric_csv.
        header = ['import csv', 'import os',
                  'print("EXECUTION FOLDER: " + os.getcwd())',
                  change_folder_line,
                  'with open("' + study_nam +
                  '.csv") as csvfile:',  # Lines to extract pars from csv
                  '    reader = csv.DictReader(csvfile)',
                  '    lines = [row for row in reader]',
                  'parameters = ' + str(parameters_list),
                  'domains = {parameter :'
                  '[k[parameter] for k in lines] for parameter in parameters}']

        # Build lines to:
        #
        # Create study, define parameters, define samples values,
        # combine samples and generate parametric jobs.
        study_lines = ['study = ParStudy(par=(parameters))',
                       'for parameter in parameters:',
                       '    study.define(DISCRETE,'
                       'par=parameter, domain=domains[parameter])',
                       'for parameter in parameters:',
                       '    study.sample(INTERVAL, interval=1, par=parameter)',
                       'study.combine(TUPLE, name=' + '"model")',
                       'study.generate(template="' + inp_file_name + '")']

        # Save output psf file.
        with open(output_psf_path, 'w') as file:
            file.write('\n'.join(header + study_lines))
            print('*** PSF file created ***')
        return output_psf_path

    def modify_inp_file(parameters_list, inp_file_name,
                        study_folde=None, analysis_folder=None,
                        **kwargs):
        """Include parameters information into a Abaqus FEA inp file.

        The algorithm modifies a inp text-like file, containing
        Abaqus FEA model information, adding lines with parametric
        information and associated necessary definitions.

        Parameters
        ----------
        parameters_list : list of str
            Variables to study during parametric analysis.
        inp_file_name : str
            Name of the inp file that defines the FEA model.
        study_folde : Path, optional
            Folder to save the output file to. If not given, the script
            assumes ./study_nam as output folder.
        analysis_folder : Path, optional
            Folder to copy output file to. Default is None.
        **kwargs : dict
            Allows to pass same argument values to different functions.

        Returns
        -------
        Path
            Full path of output inp file.
        """
        # Call inp keywords dictionary from module level.
        global INP_KEYWORDS

        # Normalize inp suffix, extract study name and set default
        # study folder.
        inp_name = Path(inp_file_name).with_suffix('.inp')
        study_nam = inp_name.stem
        if not study_folde:
            study_folde = Path(Path.cwd() / study_nam)

        # Search inp file in study folder, if not, look for it in study
        # folder and copy it to study folder.
        inp_path = Path(study_folde, inp_name)
        if inp_path.exists():
            pass
        else:
            inp_path_analysis = Path(analysis_folder, inp_name)
            shutil.copy(inp_path_analysis, inp_path)

        # Manage old version of inp file and load it
        inp_path = ft.manage_old_version_file(inp_path)
        with open(inp_path, 'r+') as file:
            lines = file.readlines()

        # Build lines to initialize parameters and insert them in inp.
        par_lines = [str(par) + '=100\n' for par in parameters_list]
        assembly_line = [(n, i) for n, i in enumerate(lines)
                         if '** ASSEMBLY' in i][0][0]
        lines[assembly_line:assembly_line] = ['* PARAMETER\n'] + par_lines

        # Build lines for parametric variables definition and insert.
        for par in parameters_list:
            for n, line in enumerate(lines):
                key = INP_KEYWORDS[par]
                if key in line:
                    after_key = line.partition(key)[-1]
                    if after_key[0] == '=':
                        lines[n] = line.replace(after_key.partition(',')[0],
                                                '=<' + par + '>')
                    else:
                        value = lines[n + 1].partition(
                            key)[-1].partition(',')[0]
                        lines[n + 1] = lines[n + 1].replace(value, '<' + par +
                                                            '>')

        # Set output inp path, save and copy it to analysis folder.
        out_inp_file = inp_path
        with open(out_inp_file, 'w+') as file:
            file.write(''.join(lines))
        if analysis_folder:
            copy_path = Path(analysis_folder, study_nam, out_inp_file.name)
            shutil.copy(out_inp_file, copy_path)
        print('*** INP file modified ***')
        return out_inp_file

    def modify_psf_4_run(psf_file_path, analysis_folder=None,
                         cpu_numbers=8, **kwargs):
        """Adds execution line to psf file, allowing Abaqus to run jobs.

        This function extract only the lines necessary to define the
        parametric study, and then adds an execution line.

        Parameters
        ----------
        psf_file_path : Path
            Psf text-like file to modify
        analysis_folder : Path, optional
            Folder to copy output file to. Default is None.
        cpu_numbers : int
           Number of cpus to be used during the execution.
        **kwargs : dict
            Allows to pass same argument values to different functions.

        Returns
        -------
        Path
            Full path of output psf file ready to execute jobs.
        """
        # Extract study name, set default output psf path and set output
        # psf file path.
        study_nam = Path(psf_file_path).stem
        out_psf = psf_file_path
        if analysis_folder:
            out_psf = Path(analysis_folder,
                           study_nam, study_nam).with_suffix('.psf')

        # Read input psf file. Gather lines of chdir to analysis folder,
        # parameters list and study definition.
        with open(psf_file_path) as input_psf:
            lines = input_psf.readlines()
        line_0 = []
        if analysis_folder:
            line_0 = [[i for i in lines if 'os.chdir' in i][0]]
        parameters_line = [[i for i in lines if 'parameters = ' in i][0]]
        study_line = [[i for i in lines if 'study = ' in i][0]]

        # Insert execution line and write output file.
        execution_line = ['study.execute(ALL, execOptions = ' +
                          '"cpus=' + str(cpu_numbers) + '")']
        with open(out_psf, 'w+') as output_file:
            output_file.write(''.join(line_0 + parameters_line
                                      + study_line + execution_line))
        return out_psf

    # Extract input data and study name. Set project sub-folder.
    input_data = ft.extract_config_from_cfg(config_file)
    study_name = config_file.stem
    study_folder = ft.create_non_existent_folder(Path.cwd() / study_name)

    # Check maximum cpu numbers. Set default inp file and analysis
    # folder. Pass data to keywords dictionary.
    max_cpu_no = multiprocessing.cpu_count()
    if ('cpu_numbers' not in input_data
            or int(input_data['cpu_numbers']) > max_cpu_no):
        input_data['cpu_numbers'] = max_cpu_no
    if 'inp_file_name' not in input_data:
        input_data['inp_file_name'] = study_name
    if 'analysis_folder' not in input_data:
        input_data['analysis_folder'] = study_folder
    input_data['study_name'] = study_name
    input_data['study_folder'] = study_folder

    # Create csv and psf files, modify inp file and run psf to obtain
    # Abaqus internal inp parametric files.
    csv_file = build_parametric_csv(study_nam=input_data['study_name'],
                                    **input_data)
    psf_file = build_parametric_psf(parametric_csv=csv_file,
                                    **input_data)
    modify_inp_file(**input_data)
    run_psf(psf_file, **input_data)

    # Modify psf file for running FEA jobs from command line.
    output_psf = modify_psf_4_run(psf_file, **input_data)
    return output_psf


def extract_fea_data(config_file):
    """Gather output data from Abaqus FEA Odb files.

    Fundamentally, the algorithm takes a basic post-process Python
    script containing Abaqus commands, and modify if to enhance it
    functionality. Then it runs it in a Abaqus subprocess and saves
    output data in numpy compressed arrays, for further analysis. They
    are saved in a temp_script sub-folder.

    This is done with batch processing in mind. The objective is to
    automatize the slower process of output gathering in parametric
    analysis.

    Parameters
    ----------
    config_file : Path
        Path of config file containing study data.

    Returns
    -------
    List of strings
       Extracted Abaqus output variable reference keywords.
    """
    def modify_gather_script(extraction_algorithm, database_folder=None,
                             one_odb_only=False, **kwargs):
        """Adds batch commands to data gathering post-process script.

        Basically, this function inserts commands to a post-process
        Abaqus script. The objective is to enhance its capacities,
        with options to chdir to a database folder, batch process
        Odb files, and import of abaqus_inside module. Output arrays
        are saved as npz files in a temp_files sub-folder.

        Parameters
        ----------
        extraction_algorithm : Path
             Post-process Python script to extract data for a Odb.
        database_folder : Path, optional
            Path of folder containing Odb files to read from.
        one_odb_only : bool, optional
            If True, pass only one odb to output script. Is useful for
            debugging purposes.
        **kwargs : dict
            Allows to pass same argument values to different functions.

        Returns
        -------
        List of strings
            Abaqus output variable reference keywords.
        """
        # Extract study folder and load post-process script.
        study_folde = extraction_algorithm.parent
        with open(extraction_algorithm, 'r+') as script:
            algo_lines = script.readlines()

        # Build header lines: import built-in modules, add chdir to
        # database folder and modules folder path.
        modules_path = str(Path(__file__).parent)
        header = ['import os', 'import sys',
                  'os.chdir(sys.argv[-1])',
                  'import csv', 'import numpy as np',
                  'sys.path.append( "' + modules_path + '")',
                  'from abaqus_inside import *']

        # Build batch lines. Pass list of odb paths, set odb files
        # closer and indent script commands.
        closer = []
        if database_folder:
            odb_list = ft.list_files_with_extension(database_folder, '.odb')
            odb_list = [str(t) for t in odb_list]
            if one_odb_only:
                odb_list = odb_list[0:1]
            odb_header = ['odb_list=' + repr(odb_list),
                          'for odb_path in odb_list:',
                          '    odb = session.openOdb(odb_path)']
            closer = ['    odb.close()']
            algo_lines = odb_header + ['    ' + x for x in algo_lines]

        # Build time history and batch odb closer lines. Look for
        # existent time history data.
        time_history, th = False, []
        for line in algo_lines:
            if 'XYDataFromHistory' in line:
                time_history = True
                break

        # Build lines for setting output npz files names, saving them
        # and returning output message trough logging. Indent lines
        # for batch.
        if time_history:
            parent_dir, npz_name = '', 'odb_name.replace(".odb",".npz")'
            th = ['data = {k: v for k, v in session.xyDataObjects.items()}',
                  'odb_name = odbs_retrieve_name(0)',
                  'npz_name = ' +
                  repr(str(study_folde / 'temp_files') + '/') +
                  ' + ' + npz_name + ".split('/')[-1]",
                  'np.savez(npz_name, **data)',
                  'log_abaqus("npz saved:")',
                  'log_abaqus(npz_name)']
            if database_folder:
                th = ['    ' + x for x in th]

        # Assembly modified script lines and save it in temp folder.
        lines_to_exec = '\n'.join(header + algo_lines + th + closer)
        temp_folder = ft.create_non_existent_folder(study_folder / 'temp_files')
        modified_script_path = Path(temp_folder,
                                    'temp_script').with_suffix('.py')
        with open(modified_script_path, 'w+') as out_file:
            out_file.write(lines_to_exec)
        print('*** GATHER SCRIPT MODIFIED ***')
        return modified_script_path

    # Read input config file. Extract study name and subfolder.
    input_cfg = ft.extract_config_from_cfg(config_file)
    study_name = config_file.stem
    study_folder = Path(Path.cwd() / study_name)

    # Build kwags dict and set default paths and post-process script.
    input_cfg['study_folde'] = study_folder
    if not input_cfg['extraction_algorithm']:
        input_cfg['extraction_algorithm'] = Path(study_folder,
                                                 study_name).with_suffix('.py')
    input_cfg['database_folder'] = Path(input_cfg['database_folder'],
                                        study_name)
    default_false_vars = ['gui', 'verbose', 'one_odb_only']
    for i in default_false_vars:
        if i not in input_cfg.keys():
            input_cfg[i] = False

    # Modify post-process script for batch and run it in subrpocess.
    modified_script = modify_gather_script(**input_cfg)
    output_vars = run_abaqus_subprocess(script=modified_script, **input_cfg)
    return output_vars


def parametric_check_odb_files(root_path):
    """Check completeness of Abaqus jobs in a parametric analysis.

    This function reads sequentially numbered Abaqus output .log files,
    corresponding to Abaqus jobs. Then it checks if output status is
    set with COMPLETED Abaqus keyword.

    Parameters
    ----------
    root_path : Path
         Folder containing log and Odb files.

    Returns
    -------
    bool
        True if no .log file is missing and if all jobs statuses are
        set as COMPLETED. False otherwise.
    """
    # List all .log files in folder.
    strings_list = ft.list_files_with_extension(root_path=root_path,
                                                extension='log',
                                                full_path=True,
                                                recursively=False)

    # Extract log files numbers and check consecutiveness.
    numbers = [st.extract_number_from_str(i) for i in
               st.sort_strings_by_digit(strings_list)]
    status_out = True
    check_files, missing_files = mt.check_array_consecutiveness(numbers)

    # Report missing files.
    if not check_files:
        print('WARNING: MODELS', missing_files, 'MISSING')
        print('CURRENT NUMBERS: ', numbers)
        status_out = False

    # Report jobs status.
    for i in strings_list:
        with open(i) as file_read:
            lines_list = file_read.readlines()
            status = lines_list[-1].split(' ')[-1]
        if status != 'COMPLETED\n':
            print('WARNING: JOB ', i, ' NOT COMPLETED')
            status_out = False

    # Report general statuses.
    print('Parametric files in ' + root_path + ' in good condition:',
          status_out)
    return status_out


def run_abaqus_subprocess(script, database_folder=None, gui=False,
                          verbose=False, **kwargs):

    """Run script in Abaqus subprocess and return data logged in it.

    If a database folder is provided, additional commands are passed,
    to chdir to that folder, in order to create temporary files there.

    Parameters
    ----------
    script : Path
         Path of script to be run.
    database_folder : Path, optional
        Path of folder containing Odb files to read from.
    gui : bool, optional
        If True, run script in GUI version of Abaqus CAE. Useful for
        debugging purposes.
    verbose : bool, optional
        If True, print gathered output variable references.
    **kwargs : dict
        Allows to pass same argument values to different functions.

    Returns
    -------
    List of strings
        Abaqus output variable reference keywords.
    """
    # Normalize script path to string. Select Abaqus executable for cmd.
    print('*** RUNNING ' + script.name + ' ***')
    script = str(script)
    if gui:
        command = 'abaqus cae script='
    else:
        command = 'abaqus cae noGUI='

    # Set command lines. If database folder given, include chdir
    # commands.
    process = command + script
    if database_folder:
        database_folder = str(database_folder)
        process = r'SET original_folder=%cd% & cd ' + database_folder + \
                  ' & ECHO %cd% & cd & ' + command + script + ' -- %cd%'

    # Launch subprocess and wait for completion
    p = subprocess.Popen(process, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    print('*** DONE EXECUTING ABAQUS SUBPROCESS ***')
    print('ERROR:', err)

    # Get Abaqus logs and print them if verbose is True. Filter output
    # variable references, strip sys argv and empy spaces.
    out_var_references = [i.decode("utf-8") for i in out.split(b'\r\n')]
    if verbose:
        pprint.pprint(out_var_references)
    paths_to_strip = [Path.cwd()]
    if database_folder:
        paths_to_strip.append(Path(database_folder))
    out_var_references = [i for i in out_var_references
                          if Path(i) not in paths_to_strip and ' ' not in i]
    return out_var_references


def run_psf(input_var, **kwargs):
    """Runs a psf file trough Abaqus command line.

    If a study project configuration file is passed as input, the
    algorithm builds Path of psf file first.

    Parameters
    ----------
    input_var : Path
        Either Path of psf file to be runnd, or config file to infer
        psf Path from.

    Returns
    -------
    None
    """
    # Build psf Path
    if Path(input_var).suffix == '.psf':
        psf_file = str(input_var)
    if Path(input_var).suffix == '.cfg':
        config_data = ft.extract_config_from_cfg(input_var)
        psf_file = str(Path(config_data['analysis_folder'],
                            input_var.stem, input_var.stem).with_suffix('.psf'))

    # Run psf file in no-GUI environment and wait for it to finish
    print('RUNING', psf_file)
    p = subprocess.Popen('abaqus script=' + psf_file, shell=True)
    p.communicate()


def summarize_fea_output(config_file):
    """Organize and store Abaqus output data files in a hdf5 database.

    The algorithm reads npz files containing Abaqus output data,
    organize them in groups after each output variable and save them
    in a hdf5 database file.

    Each hdf5 dataset is an Abaqus output numpy array. The function
    assigns attributes to each of the datasets, taken them from a
    parametric csv file that contains values of parameters of each
    model.

    Parameters
    ----------
    config_file : Path
        Path of config file containing study data.

    Returns
    -------
    output_path : Path
        Path of output hdf5 file.
    """
    # Extract study name, set input folder and csv and output hdf5 file.
    study_name = Path(config_file).stem
    temp_folder = Path(Path.cwd() / study_name / 'temp_files')
    csv_file = Path(config_file).with_suffix('.csv')
    hdf_path = Path(config_file).with_suffix('.hdf5')

    # Read config file for printing output structure option.
    input_config = ft.extract_config_from_cfg(config_file)

    # Extract parametric data from csv, set models names as
    # data-frame index and convert it to dict.
    df = pd.read_csv(csv_file)
    df.set_index('MODEL_NO', inplace=True)
    df_dict = df.to_dict(orient='index')
    for k, v in df_dict.items():
        v['MODEL_NO'] = str(k)

    # Save npz files to hdf5 file. Reload hdf5 file to reorder internal
    # structure, using output variable references as group keys.
    npz_files_paths = ft.list_files_with_extension(temp_folder, '.npz')
    db.save_npz_in_hdf5(npz_files_list=npz_files_paths, hdf5_path=hdf_path,
                        attributes_dict=df_dict,
                        verbose=input_config['print_hdf5'])
    temp_hdf_path = Path(hdf_path.parent, 'temp_files', hdf_path.name)
    db.restructure_hdf5_file(hdf_path, output_path=temp_hdf_path)
    shutil.copy(temp_hdf_path, hdf_path)
    print('*** HDF5 file created ***')
    return hdf_path

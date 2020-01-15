""" Functions related to Abaqus, to be used by an external Python interpreter.
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""

import configparser
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


def parametric_check_odb_files(root_path):
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


def parametric_analysis(config_file):
    """
    Generate files necessary for parametric analysis within abaqus.
    Input: config_file. Path of config file for the study.
    """
    # Config input file
    config_file_path = config_file
    cfg = configparser.ConfigParser()
    cfg.read(config_file_path)

    # Extract input data and process it
    section = 'PARAMETRIC_ANALYSIS'
    parameter_values_file = cfg.get(section, 'PARAMETER_VALUES_FILE')
    parameters_list = eval(cfg.get(section, 'PARAMETERS'))
    template_file = cfg.get(section, 'TEMPLATE_FILE').replace('.inp', '')
    execute_jobs = cfg.get(section, 'EXECUTE_JOBS')
    try:
        import multiprocessing
        max_cpu_numbers = multiprocessing.cpu_count()
        cpu_numbers = cfg.get(section, 'CPU_NUMBERS')
        if cpu_numbers > max_cpu_numbers:
            cpu_numbers = max_cpu_numbers
    except configparser.NoOptionError:
        cpu_numbers = max_cpu_numbers
    try:
        inp_folder = cfg.get(section, 'INP_FOLDER')
        input_folder = cfg.get(section, 'INPUT_FOLDER')
        output_folder = cfg.get(section, 'OUTPUT_FOLDER')
    except KeyError:
        inp_folder, input_folder, output_folder = None, None, None

    psf_file = parametric_psf(parameter_values_file, parameters_list, template_file, input_folder=input_folder,
                              output_folder=output_folder, cpu_numbers=cpu_numbers, execute_jobs=execute_jobs)
    inp_file = parametric_modify_inp(template_file + '.inp', parameters_list,
                                     inp_folder=inp_folder, output_folder=output_folder)

    run_psf(psf_file)


def parametric_psf(parameter_values_file, parameters_list, template_file, input_folder=None, output_folder=None,
                   cpu_numbers=4, execute_jobs=0):
    """
    Create *.psf file, for parametric analysis from abaqus command line.
    Input: parameter_values_file. Csv file containing input variables values.
           parameters_list. List of parameters for the study.
           template_file. Inp file which defines the FEA model.
           output_folder. Path of output files. If not provided, look for inp file in current folder.
           cpu_numbers. Number of CPUs for job paralellization.
           execute_jobs. If 1, execute created jobs.
    Output: Path of psf file.
    """
    parameter_file_path = parameter_values_file
    if input_folder:
        parameter_file_path = input_folder + parameter_values_file
    output_psf_file = parameter_values_file.replace('.csv', '') + '.psf'
    if output_folder:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        output_psf_file = output_folder + output_psf_file
    header = ['import csv',
              'with open("' + parameter_file_path + '") as csvfile:',
              '    reader = csv.DictReader(csvfile)',
              '    lines = [row for row in reader]',
              'parameters = ' + str(parameters_list),
              'domains = {parameter : [k[parameter] for k in lines] for parameter in parameters}']
    with open(output_psf_file, 'w') as file:
        # Header
        for line in header:
            file.write(line)
            file.write('\n')
        if output_folder:
            file.write('import os\n')
            file.write('os.chdir("' + output_folder + '")\n')
        # Create study
        file.write('study = ParStudy(par=(parameters))\n')
        # Define the parameters
        file.write('for parameter in parameters:\n')
        file.write('    study.define(DISCRETE, par=parameter, domain=domains[parameter])\n')
        # Sampling
        file.write('for parameter in parameters:\n')
        file.write('    study.sample(INTERVAL, interval=1, par=parameter)\n')
        # Combine the samples
        file.write('study.combine(TUPLE, name=' + "'model')\n")
        # Generate jobs
        file.write('study.generate(template="' + template_file + '")\n')
        # Execute jobs
        if int(execute_jobs):
            file.write('study.execute(ALL, execOptions = ' + "'cpus=" + str(cpu_numbers) + "')\n")
        print('*** PSF file created ***')
    return output_psf_file


def parametric_modify_inp(inp_file, parameters_list, inp_folder=None, output_folder=None):
    """
    Modify inp file, to include parameters information.
    Input: inp_file. Inp file to be modified.
           parameters_list. List of parameters for the study.
           inp_folder. Path of inp folder location. If not provided, look for inp file in current folder.
           output_folder. Path of output files. If not provided, look for inp file in current folder.
    Output: Path of inp file.
    """
    inp_variables_names = {'ALPHA_DYN': 'Dynamic,alpha', 'E': 'Elastic'}
    if inp_folder:
        inp_file = inp_folder + inp_file
    with open(inp_file, 'r+') as file:
        lines = file.readlines()
    # Initialize parameters
    assembly_line = [(n, i) for n, i in enumerate(lines) if '** ASSEMBLY' in i]
    assembly_line_n = assembly_line[0][0]
    parameters_head_line = ['* PARAMETER\n']
    parameters_lines = [str(parameter) + '=100\n' for parameter in parameters_list]
    lines = lines[0:assembly_line_n] + parameters_head_line + parameters_lines + lines[assembly_line_n:]
    for parameter in parameters_list:
        for n, line in enumerate(lines):
            if inp_variables_names[parameter] in line:
                try:
                    a = line.split(inp_variables_names[parameter])[-1].split(',')[1]
                    value = line.split(inp_variables_names[parameter])[-1].split(',')[0]
                    lines[n] = line.replace(value, '=<' + parameter + '>')
                except IndexError:
                    value = lines[n+1].split(inp_variables_names[parameter])[-1].split(',')[0]
                    lines[n+1] = lines[n+1].replace(value, '<' + parameter + '>')
    if output_folder:
        inp_file = output_folder + inp_file.replace(inp_folder, '')
    with open(inp_file, 'w+') as file:
        for line in lines:
            file.write(line)
    print('*** INP file modified ***')
    return inp_file


def run_psf(psf_file):
    """
    Runs parametric analysis in a separate cmd window.
    Input: psf_file. Path of psf file.
    """
    os.system('abaqus script=' + psf_file)


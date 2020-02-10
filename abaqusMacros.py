""" Macros functions to be used in Abaqus environment.
    abaqusMacros.cfg file is expected to be in the same folder as
    this script.
    Ideally, put both in the /site folder of your Abaqus installation,
    otherwise you could place them in the working directory, but if
    the interpreter switches to another directory, it won't be able
    to read the macros.
    
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""
from __future__ import print_function
from abaqus import *
from abaqusConstants import *
import __main__
import ConfigParser as configparser


config_file_path = __file__.replace('.py', '.cfg').replace('.pyc', '.cfg').replace('.cfgc', '.cfg')
cfg = configparser.ConfigParser()                                                # Start configfile engine
cfg.read(config_file_path)                                                       # Read input file
CPUS_NUMBER = eval(cfg.get('MACROS', 'CPUS_NUMBER'))                             # Extract input data and process it


def jobs_create_4all_models():
    """
    Creates a Job for every Model in the Database, if it doesn`t exist yet,
    with the assigned characteristics.
    """
    global CPUS_NUMBER
    for model_key, model in mdb.models.items():
        model_name = model_key.replace(' ', '_')                                 # Replace blank spaces for underscores
        if model_name not in mdb.jobs.keys():                                    # Create the Job using each Model name
            jobs_create_4all_models_with_overwrite()
    return


def jobs_create_4all_models_with_overwrite():
    """
    Creates a Job for every Model in the Database, with the
    assigned characteristics.
    """
    global CPUS_NUMBER
    for model_key, model in mdb.models.items():
        model_name = model_key.replace(' ', '_')                                 # Replace blank spaces for underscores
        mdb.Job(name=str(model_name), model=model, description='',               # Create the Job using each Model name
                type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0,
                queue=None, memory=90, memoryUnits=PERCENTAGE,
                getMemoryFromAnalysis=True, explicitPrecision=SINGLE,
                nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
                contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT,
                numCpus=CPUS_NUMBER, numDomains=CPUS_NUMBER)
    return


def jobs_run_all():
    """ Runs all the Jobs contained in the Database, one at a time. """
    jobs_count = 1
    for job_key, job in mdb.jobs.items():                                        # Iterate trough Model Jobs
        job.submit(consistencyChecking=OFF)                                      # Run job
        print('Job number ', str(jobs_count), ' of: ', str(len(mdb.jobs)))       # Report job number and remaining
        job.waitForCompletion()                                                  # Wait for completion
        jobs_count += 1
    return


def jobs_run_not_completed():
    """ Runs all Jobs contained in the Database which status in not
        COMPLETED, one at a time. """
    jobs_count = 1
    for job_key, job in mdb.jobs.items():                                        # Iterate trough Model Jobs
        if job.status != COMPLETED:                                              # Verify job status
            job.submit(consistencyChecking=OFF)                                  # If not Completed, run it
            print('Job number ', str(jobs_count))                                # Report job number and remaining
            job.waitForCompletion()                                              # Wait for completion
            jobs_count += 1
    return


def models_replace_blank_spaces():
    """ Replaces all blank spaces in the names of the Models
        present in the current Database for underscores. """
    for model_key in mdb.models.keys():
        mdb.models.changeKey(fromName=model_key,
                             toName=model_key.replace(" ", "_"))
    return


def odbs_close_all_odbs():
    """ Closes all Odbs that are open on the current Session. """
    for odb_key, odb in session.odbs.items():
        odb.close()
    return


def xydata_clean_all_xydata():
    """ Erases all xyData from the current Session """
    for xydata_key, xydata in session.xyDataObjects.items():
        del xydata
    return


def xyplots_clean_all_xyplots():
    """ Erases all xyPlots from the current Session. """
    for xyplot_key, xyplot in session.xyPlots.items():
        del xyplot
    return

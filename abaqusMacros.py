"""Macros functions to be called within Abaqus CAE session.

    Configuration abaqusMacros.cfg file is expected to be in the same
    folder as this script. Ideally, both should be located the /site
    folder of SIMULIA Abaqus installation. They can also be placed in
    the working directory, but if the interpreter switches to another
    folder, it won't be able to this file.

    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392

    """

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
import __main__

import ConfigParser as configparser


# Set configuration file path, read it and load configuration data.
config_file_path = __file__.replace('.py', '.cfg').replace('.pyc', '.cfg')
config_file_path = config_file_path.replace().replace('.cfgc', '.cfg')
cfg = configparser.ConfigParser()
cfg.read(config_file_path)
CPUS_NUMBER = eval(cfg.get('MACROS', 'CPUS_NUMBER'))


def clean_all_xydata():
    """Delete all xyData in current Session """
    for xydata_key, xydata in session.xyDataObjects.items():
        del xydata
    return


def clean_all_xyplots():
    """Delete all xyPlots in current Session """
    for xyplot_key, xyplot in session.xyPlots.items():
        del xyplot
    return


def close_all_odbs():
    """Close all opened Odb objects in current Session."""
    for odb_key, odb in session.odbs.items():
        odb.close()
    return


def create_jobs_not_overwriting():
    """Create a job for each model in database, without overwriting."""
    global CPUS_NUMBER

    # Iterate over models in current database and create a job for each
    # of them model, naming it the same as the model name, replacing
    # any blank spaces for underscores.
    for model_key, model in mdb.models.items():
        model_name = model_key.replace(' ', '_')
        if model_name not in mdb.jobs.keys():
            create_jobs_overwriting()
    return


def create_jobs_overwriting():
    """Create a job for each model in database, with overwriting."""
    global CPUS_NUMBER

    # Iterate over models in current database and create a job for each
    # of them model, naming it the same as the model name, replacing
    # any blank spaces for underscores.
    for model_key, model in mdb.models.items():
        model_name = model_key.replace(' ', '_')
        mdb.Job(name=str(model_name), model=model, description='',
                type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0,
                queue=None, memory=90, memoryUnits=PERCENTAGE,
                getMemoryFromAnalysis=True, explicitPrecision=SINGLE,
                nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
                contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT,
                numCpus=CPUS_NUMBER, numDomains=CPUS_NUMBER)
    return


def replace_models_names_blanks():
    """Replace blank for underscores in all models names."""
    for model_key in mdb.models.keys():
        mdb.models.changeKey(fromName=model_key,
                             toName=model_key.replace(" ", "_"))
    return


def run_all_jobs():
    """Run all jobs in current database, one at a time."""
    # Iterate over jobs, run them, report and wait for completion.
    jobs_count = 1
    for job_key, job in mdb.jobs.items():
        job.submit(consistencyChecking=OFF)
        print('Job number ', str(jobs_count), ' of: ', str(len(mdb.jobs)))
        job.waitForCompletion()
        jobs_count += 1
    return


def run_not_completed_jobs():
    """Run all not completed jobs in current database, one at a time."""
    # Iterate over jobs, run them, report and wait for completion.
    jobs_count = 1
    for job_key, job in mdb.jobs.items():

        # Verify job status. Pass if already completed.
        if job.status != COMPLETED:
            job.submit(consistencyChecking=OFF)
            print('Job number ', str(jobs_count))
            job.waitForCompletion()
            jobs_count += 1
    return

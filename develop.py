"""Temporal developing functions to be called by Abaqus CAE.

    Any functionality being developed for its use within Abaqus
    interpreter can be placed in this script, as this file can be
    modified on the fly and called again for testing, without having to
    close and open an new Abaqus session.

    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392

    """

print('***** EXECUTING DEVELOP FILE *****')
#import abaqus_inside
import collections
import tools_submodule.filesystem_tools as ft
import abaqus_outside as abo
import pprint
import os


def models_upgrade_from_folder(models_folder, recursive=False, print_every=1):
    """
    Upgrades all Mdb objects in models_folder to current Abaqus CAE version.
    Inputs: models_folder. Folder to fetch Mdb objects from.
            recursive. Boolean, if True, search for Mdb objects recursively.
            print_every. Int that defines intervals for printing info.
    """
    models_list = ft.files_with_extension_lister(models_folder, '.cae', full_name_option=True,
                                                 sub_folders_option=recursive)
    #upgradable_models_list = [i for i in models_list if odbAccess.isUpgradeRequiredForMdb(i)]
    print(len(models_list), 'Mdb objects found', len(models_list), 'require upgrade')
    temp_name = os.path.join(models_folder, 'temp_mdb_name.cae')
    for job_number, model_key in enumerate(models_list):
        # Option to print less
        if divmod(job_number, print_every)[1]==0:
            print('Processing', model_key, job_number + 1, 'of', len(models_list))
        new_name = model_key
        old_name = model_key.replace('.cae', '-old.cae')
        print(('acaaaaaa', model_key, temp_name))
        upgradeMdb(r'C:\abaqus_data\Models\Contact\BLOCKS_CONTACT.cae', temp_name)
        # Rename old and new Odb files
        os.rename(model_key, old_name)
        os.rename(temp_name, new_name)
    print('DONE')
    return


#c = modify_gather_script(r'C:\abaqus_temp\abaqus_scripts/IDL_2D_1M_ALPHA_DYN.py',
#                         'C:/abaqus_results/IDL_2D_1M_ALPHA_DYN', 1)
#run_abaqus_subprocess(c, gui=0, analysis_folder=r'C:/abaqus_results', verbose=1)

#to_run = abo.parametric_create_files('IDL_2D_1M_ALPHA_DYN.cfg')
#abo.run_psf(to_run)

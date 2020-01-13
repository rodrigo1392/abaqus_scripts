print('***** EXECUTING DEVELOP FILE *****')
import abaqus_inside
import collections


def models_upgrade_from_folder(models_folder, recursive=False, print_every=1):
    """
    Upgrades all Mdb objects in models_folder to current Abaqus CAE version.
    Inputs: models_folder. Folder to fetch Mdb objects from.
            recursive. Boolean, if True, search for Mdb objects recursively.
            print_every. Int that defines intervals for printing info.
    """
    models_list = files_with_extension_lister(models_folder, '.cae', full_name_option=True, sub_folders_option=recursive)
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
    
    
import os
#a=os.getcwd()
#print(a)

a = models_upgrade_from_folder(r'C:\abaqus_data\Models\Contact', 0)
print(a, type(a))

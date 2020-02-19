import os
from tools_submodule import filesystem_tools as ft
from tools_submodule import strings_tools as st
from tools_submodule import databases_tools as db
import abaqus_outside as abo
from pathlib import Path
import developing

# Input Config file managing
MAIN_SCRIPT_FULL_PATH = Path(os.path.realpath(__file__))
MAIN_FOLDER_PATH = MAIN_SCRIPT_FULL_PATH.parent
MAIN_CONFIG_FILE = Path(MAIN_SCRIPT_FULL_PATH).with_suffix('.cfg')
CONFIG_PROJECTS = ft.extract_config_from_cfg(MAIN_CONFIG_FILE)

# Iterate over studies
for STUDY_NUM, STUDY_NAME in enumerate(CONFIG_PROJECTS['study_names']):
    STUDY_CONFIG_FILE = Path(MAIN_FOLDER_PATH,
                             STUDY_NAME, STUDY_NAME).with_suffix('.cfg')
    if CONFIG_PROJECTS['create_parametric_files'][STUDY_NUM]:
        PAR_FILES = abo.create_parametric_files(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['run_parametric_analysis'][STUDY_NUM]:
        abo.run_psf(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['extract_fea_output'][STUDY_NUM]:
        abo.extract_fea_data(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['summarize_output'][STUDY_NUM]:
        abo.summarize_fea_output(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['post_process'][STUDY_NUM]:
        developing.post_process(STUDY_CONFIG_FILE)

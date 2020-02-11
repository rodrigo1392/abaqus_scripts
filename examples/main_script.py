import os
from tools_submodule import filesystem_tools as ft
from tools_submodule import strings_tools as st
from tools_submodule import databases_tools as db
from abaqus_outside import run_psf, parametric_create_files, parametric_extract_fea_data,parametric_summarize_output
import multiprocessing, numpy as np, pandas as pd, shutil, subprocess, pprint
from pathlib import Path
import h5py
import re
import json
import matplotlib.pyplot as plt
from tools_submodule.strings_tools import list_of_lists_unique


def hdf5_meta_dict(hd_db):
    """
    Get first level keys and attributes of a hdf5 file.
    Input: Path of dhf5 file.
    Output: Tuple of List of keys, List of attributes
    """
    with h5py.File(hd_db, 'r') as db_file:
        m_keys = list_of_lists_unique([v.keys() for v in db_file.values()])
        m_attrs = list_of_lists_unique([i.attrs.keys() for i in db_file.values()])
    return m_keys, m_attrs


def plot_from_hdf5(hd_db):
    with h5py.File(hd_db, 'r') as opened:
        keys = hdf5_meta_dict(hd_db)[0]
        sorted_keys = st.sort_strings_by_digit(list(keys))
        for key, value in opened.items():
            for model_n, model in enumerate(sorted_keys):
                if model_n == 0 or model_n == 19:
                    data = value[model]
                    leg = round(data.attrs['ALPHA_DYN'], 3)
                    plt.plot(data[:, 0], data[:, 1], label=leg)
            plt.title(key)
            plt.legend()
            plt.show()


def post_process(config_file):
    study_name = Path(config_file).stem
    study_folder = Path.cwd() / study_name
    hdf_db = (study_folder / study_name).with_suffix('.hdf5')
    plot_from_hdf5(hdf_db)


# Input Config file managing
MAIN_SCRIPT_FULL_PATH = Path(os.path.realpath(__file__))
MAIN_FOLDER_PATH = MAIN_SCRIPT_FULL_PATH.parent
MAIN_CONFIG_FILE = Path(MAIN_SCRIPT_FULL_PATH).with_suffix('.cfg')
CONFIG_PROJECTS = ft.config_file_extract_input(MAIN_CONFIG_FILE)

# Iterate over studies
for STUDY_NUM, STUDY_NAME in enumerate(CONFIG_PROJECTS['study_names']):
    STUDY_CONFIG_FILE = Path(MAIN_FOLDER_PATH, STUDY_NAME, STUDY_NAME).with_suffix('.cfg')
    if CONFIG_PROJECTS['create_parametric_files'][STUDY_NUM]:
        PAR_FILES = parametric_create_files(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['run_parametric_analysis'][STUDY_NUM]:
        run_psf(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['extract_fea_output'][STUDY_NUM]:
        parametric_extract_fea_data(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['summarize_output'][STUDY_NUM]:
        parametric_summarize_output(STUDY_CONFIG_FILE)
    if CONFIG_PROJECTS['post_process'][STUDY_NUM]:
        post_process(STUDY_CONFIG_FILE)

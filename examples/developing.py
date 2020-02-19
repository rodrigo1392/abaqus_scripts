from pathlib import Path
import h5py
from collections import defaultdict
from tools_submodule import strings_tools as st
from matplotlib import pyplot as plt


def post_process(config_file):
    """Show first level groups keys and attributes on a hdf5 file.

    Parameters
    ----------
    hdf5_path : Path
        Hdf5 file to be investigated.

    Returns
    -------
    List of str
        Keys of first level groups.
    List of str
        Attributes names of first level groups.
    """
    study_name = Path(config_file).stem
    study_folder = Path.cwd() / study_name
    hdf_db = (study_folder / study_name).with_suffix('.hdf5')
    a = plot_from_hdf5(hdf_db, [1, 20])
    #print(a)
    plot_from_dict(a)


def plot_from_hdf5(hd_db, models_range=None):
    plots_dict = {}
    with h5py.File(hd_db, 'r') as opened:
        for variable, arrays_group in opened.items():
            plots_dict[variable] = []
            models_keys = st.sort_strings_by_digit(list(arrays_group))

            if models_range is None:
                models_range = range(1, len(models_keys) + 1)
            if isinstance(models_range, tuple):
                models_range = range(models_range[0], models_range[-1] + 1)

            for key in models_keys:
                curve_dict = defaultdict(lambda: None)
                data = arrays_group[key]
                model_no = int(data.attrs['MODEL_NO'])
                if model_no in models_range:
                    curve_dict['data'] = data[:, 0], data[:, 1]
                    curve_dict['legend'] = round(data.attrs['ALPHA_DYN'], 3)
                    plots_dict[variable].append(curve_dict)
    return plots_dict


def plot_from_dict(plots_dict):
    for plot_title, plot_dict in plots_dict.items():
        curves_group = plot_dict
        for curve_dict in curves_group:
            cd = curve_dict
            plt.plot(cd['data'][0], cd['data'][1], label=cd['legend'])
        plt.title(plot_title)
        plt.legend()
        plt.show()
# Abaqus scripts
Python scripts to automate the boring stuff in everyday use of Simulia Abaqus

# Launching Abaqus CAE
The open_abaqus.bat launches Abaqus CAE and calls for open_abaqus.py script. You can create a link for the bat file and put it on the desktop for easier acces.
The open python script does several things:

- Modifies visuatization options.
- Changes work directory to the one specified in the config_abaqus.cfg file
- Imports abaqus_inside module, which containts functions to be used within Abaqus itself.
- Optionally: opens a default file at start, imports "develop.py" file and assigns it to a function named dev, so you can easily modify snippets and run them by calling "dev()" in Abaqus CAE command area.


# Macros

Macros to be used in the CAE mode of Simulia Abaqus.

You should place both abaqusMacros.py and abaqusMacros.cfg files in the "site" directory of your installation, commonly, in C:\SIMULIA\CAE\2020\win_b64\SMA\site. This is required so Abaqus can find the files even when the 'Work directory' is changed during the CAE session. If you don't plan to do that, then keeping both on Work directory should be OK.

The .cfg file contains inputs parameters to some of the macros scripts, present in abaqusMacros.py. You can config them on the fly, by saving changes on cfg file and then hitting the Reload button in the File->Macro manager dialog box on the GUI.


# Parametric analysis

In this framework, parametric analysis is thought as a 6 steps process, which are intented to be as automatized as posible. They are:

1. Creation of input psf and inp files required by Abaqus CAE, and an auxiliar csv file with parameters samples values. It requires a cfg config file with mathematical details of the parametric project and a template inp of the FEA model.

2. Run simulations from an auxiliar command line.

3. Extract output data and save it as npz numpy arrays, one for each odb file in the project. An script to read and generate time history and field data is required. It can be created manually, studying the rpy file generated automatically by Abaqus when performing actions in the GUI software.

4. Summarize output data calling all npz files, ordinate them and save the database in a hdf5 file.

5. Read hdf5 file and export data, create plots, etc.

Parametric functions, present in abaqus_outside script, are designed to be used during each of these steps. An example of input cfg and inp files are provided in examples folder.

# Looking forward to keep including new actions. All sugestions are welcome.

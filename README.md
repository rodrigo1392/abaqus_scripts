# Abaqus scripts

Python scripts to automate the boring stuff in everyday use of Simulia Abaqus


# Macros

Macros to be used in the CAE mode of Simulia Abaqus.

You should place both abaqusMacros.py and abaqusMacros.cfg files in the "site" directory of your installation, commonly, in C:\SIMULIA\CAE\2019\win_b64\SMA\site. This is required so Abaqus can find the files even when the 'Work directory' is changed during the CAE session. If you don't plan to do that, then keeping both on Work directory should be OK.

The .cfg file contains inputs parameters to some of the macros scripts, present in abaqusMacros.py. You can config them on the fly, by saving changes on cfg file and then hitting the Reload button in the File->Macro manager dialog box on the GUI.

Looking forward to keep including new actions.

All sugestions are welcome.

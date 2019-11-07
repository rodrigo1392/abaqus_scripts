# abaqus_macros
Macros to be used in the CAE mode of Simulia Abaqus.

You should place both abaqusMacros.py and abaqusMacros.cfg files in the "site" directory of your installation, commonly, in C:\SIMULIA\CAE\2019\win_b64\SMA\site. This is required so Abaqus can find the files even when the 'Work directory' is changed during the CAE session. If you don't plan to modify Working directory, then keeping both on it should be OK.

The .cfg file is used to mofify the behaviour of macros scripts, present in abaqusMacros.py.

You can modify config variables on the fly, by saving changes on cfg file and then hitting the Reload button in
the File->Macro manager dialog box on the GUI.

Looking forward to keep including new actions.

All sugestions are welcome.

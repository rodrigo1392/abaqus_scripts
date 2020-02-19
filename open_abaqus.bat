REM Open an Abaqus CAE session and run open_abaqus.py script.
SET configfile=open_abaqus_config_file.cfg
for /F "tokens=*" %%I in (%configfile%) do SET %%I
SET original_folder=%cd%
cd %WORK_DIRECTORY%
abaqus cae script=%original_folder%/open_abaqus.py -- %configfile%, %original_folder%
pause
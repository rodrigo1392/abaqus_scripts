"""Open Abaqus CAE with configuration options and added functionality.

    This script may be edited using appropriate keywords from Abaqus
    documentation.

    Configuration open_abaqus_config_file.cfg file is expected to be in
    the same folder as this script.

    It should contain the absolute path of working folder, to chdir to
    after inialization.

    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392

    """

import os
import sys

abaqus_scripts_folder = sys.argv[-1]
config_file_name = sys.argv[-2].replace(',', '').replace('/', '')

sys.path.insert(0, abaqus_scripts_folder)
from abaqus_inside import *
from tools_submodule import filesystem_tools as ft


def visualization_config():
    # Define fonts config.
    legend_font = '-*-verdana-medium-r-normal-*-*-110-*-*-p-*-*-*'
    state_font = '-*-verdana-medium-r-*-*-*-120-*-*-*-*-iso8859-1'
    title_font = '-*-verdana-medium-r-*-*-*-120-*-*-*-*-iso8859-1'
    triad_font = '-*-verdana-bold-r-normal--25-*'

    # Set Abaqus visual configuration.
    session.graphicsOptions.setValues(antiAlias=ON,
                                      dragMode=FAST,
                                      autoFitAfterRotate=OFF,
                                      translucencyMode=5)
    session.viewports['Viewport: 1']. \
        assemblyDisplay.setValues(optimizationTasks=OFF,
                                  geometricRestrictions=OFF,
                                  stopConditions=OFF)
    session.viewports['Viewport: 1']. \
        odbDisplay.setValues(_useDefaultOptions=OFF)
    session.viewports['Viewport: 1']. \
        odbDisplay.basicOptions.setValues(numericForm=REAL)
    session.viewports['Viewport: 1']. \
        odbDisplay.basicOptions.setValues(averageElementOutput=False,
                                          curveRefinementLevel=EXTRA_COARSE,
                                          otherSymbolSize=11)
    session.viewports['Viewport: 1']. \
        odbDisplay.commonOptions.setValues(visibleEdges=ALL)
    session.viewports['Viewport: 1']. \
        odbDisplay.contourOptions.setValues(showMinLocation=ON,
                                            showMaxLocation=ON,
                                            contourStyle=CONTINUOUS,
                                            numIntervals=14,
                                            intervalValues=())
    session.viewports['Viewport: 1']. \
        partDisplay.setValues(activeCutName='Z-Plane',
                              viewCut=ON)
    session.viewports['Viewport: 1']. \
        view.setProjection(projection=PARALLEL)
    session.viewports['Viewport: 1']. \
        viewportAnnotationOptions.setValues(annotations=OFF,
                                            compass=OFF,
                                            compassScale=0.8,
                                            compassPrivilegedPlane=XZPLANE,
                                            legend=ON,
                                            legendBackgroundColor='White',
                                            legendBackgroundStyle=TRANSPARENT,
                                            legendBox=OFF,
                                            legendDecimalPlaces=2,
                                            legendFont=legend_font,
                                            legendMinMax=OFF,
                                            legendNumberFormat=ENGINEERING,
                                            legendPosition=(2, 80),
                                            legendTextColor='#000000',
                                            state=OFF,
                                            stateBackgroundColor='White',
                                            stateBackgroundStyle=MATCH,
                                            stateFont=state_font,
                                            stateBox=OFF,
                                            statePosition=(13, 12),
                                            stateTextColor='White',
                                            title=OFF,
                                            titleBackgroundColor='White',
                                            titleBackgroundStyle=MATCH,
                                            titleBox=OFF,
                                            titleFont=title_font,
                                            titlePosition=(13, 20),
                                            titleTextColor='White',
                                            triad=OFF,
                                            triadColor='White',
                                            triadFont=triad_font,
                                            triadLabels=NUMBERS,
                                            triadPosition=(6, 12),
                                            triadSize=4)


# Load visualization options.
visualization_config()

# Read input data.
config_file = abaqus_scripts_folder + '/' + config_file_name
CONFIG = ft.extract_config_from_cfg(config_file)

# Open default file (Model or Odb).
if CONFIG['open_default_file'] and CONFIG['default_file']:
    print('OPENING', CONFIG['default_file'])
    if '.odb' in CONFIG['default_file']:
        try:
            o1 = session.openOdb(name=CONFIG['default_file'])
            session.viewports['Viewport: 1']. \
                setValues(displayedObject=o1)
            session.viewports['Viewport: 1']. \
                odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF,))
            ODB = session.odbs[CONFIG['default_file']]
        except:
            print('COULD NOT OPEN', CONFIG['default_file'])
            pass
    else:
        openMdb(pathName=CONFIG['default_file'])

# Load develop file and assign it to dev() function.
develop_file = abaqus_scripts_folder + '/' + CONFIG['develop_file']
if CONFIG['import_develop_file']:
    def dev():
        execfile(str(develop_file))

# Execute initial script.
if CONFIG['execute_script']:
    print('EXECUTING', CONFIG['script_2_execute'])
    execfile(abaqus_scripts_folder + '/'
             + CONFIG['script_2_execute'].replace('.py', '') + '.py')
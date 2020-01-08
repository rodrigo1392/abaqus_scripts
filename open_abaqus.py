""" Opens Abaqus CAE with personalized visualization options.
    You may edit them using appropiate keywords that you will
    find on the software documentation.
    confi_abaqus.cfg file is expected to be in the same folder as
    this script.
    It should contain the absolute path of working folder.
    Developed by Rodrigo Rivero.
    https://github.com/rodrigo1392"""

from __future__ import print_function
from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import *
import ConfigParser as configparser
import os
from abaqus_inside import *


# Config input file
config_file_path = 'open_abaqus_config_file.cfg'
cfg = configparser.ConfigParser()
cfg.read(config_file_path)

# Extract input data and process it
WORK_PATH = cfg.get('PATHS', 'WORK_DIRECTORY')
OPEN_DEFAULT_FILE = eval(cfg.get('PATHS', 'OPEN_DEFAULT_FILE'))
EXECUTE_SCRIPT = eval(cfg.get('PATHS', 'EXECUTE_SCRIPT'))
IMPORT_DEVELOP_FILE = eval(cfg.get('PATHS', 'IMPORT_DEVELOP_FILE'))
DEFAULT_FILE = cfg.get('PATHS', 'DEFAULT_FILE')
SCRIPT_2_EXECUTE = cfg.get('PATHS', 'SCRIPT_2_EXECUTE').replace('.py', '') + '.py'
PATH_TO_SCRIPT = os.path.realpath(SCRIPT_2_EXECUTE)
DEVELOP_FILE = cfg.get('PATHS', 'DEVELOP_FILE')


if OPEN_DEFAULT_FILE and DEFAULT_FILE:
    print('OPENING', DEFAULT_FILE)
    if '.odb' in DEFAULT_FILE:
        try:
            o1 = session.openOdb(name=DEFAULT_FILE)
            session.viewports['Viewport: 1'].setValues(displayedObject=o1)
            session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
            ODB = session.odbs[DEFAULT_FILE]
        except:
            print('COULD NOT OPEN', DEFAULT_FILE)
            pass

if IMPORT_DEVELOP_FILE:
    DEVELOP = DEVELOP_FILE

# Visualization config
#session.animationController.animationOptions.setValues(frameRate=55) #, relativeScaling=FULL_CYCLE)
session.graphicsOptions.setValues(antiAlias=ON, dragMode=FAST, autoFitAfterRotate=OFF, translucencyMode=5)
session.viewports['Viewport: 1'].assemblyDisplay.setValues(optimizationTasks=OFF,
                                                           geometricRestrictions=OFF,
                                                           stopConditions=OFF)
session.viewports['Viewport: 1'].odbDisplay.setValues(_useDefaultOptions=OFF)
session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(averageElementOutput=False,
                                                                   curveRefinementLevel=EXTRA_COARSE,
                                                                   otherSymbolSize=11)
session.viewports['Viewport: 1'].odbDisplay.commonOptions.setValues(visibleEdges=ALL)
session.viewports['Viewport: 1'].odbDisplay.contourOptions.setValues(showMinLocation=ON,
                                                                     showMaxLocation=ON,
                                                                     contourStyle=CONTINUOUS,
                                                                     numIntervals=14,
                                                                     intervalValues=())
session.viewports['Viewport: 1'].partDisplay.setValues(activeCutName='Z-Plane', viewCut=ON)
session.viewports['Viewport: 1'].view.setProjection(projection=PARALLEL)
session.viewports['Viewport: 1'].viewportAnnotationOptions.\
    setValues(annotations=OFF,
              compass=OFF,
              compassScale=0.8,
              compassPrivilegedPlane=XZPLANE,
              legend=ON,
              legendBackgroundColor='White',
              legendBackgroundStyle=TRANSPARENT,
              legendBox=OFF,
              legendDecimalPlaces=2,
              legendFont='-*-verdana-medium-r-normal-*-*-110-*-*-p-*-*-*',
              legendMinMax=OFF,
              legendNumberFormat=ENGINEERING,
              legendPosition=(2, 80),
              legendTextColor='#000000',
              state=OFF,
              stateBackgroundColor='White',
              stateBackgroundStyle=MATCH,
              stateFont='-*-verdana-medium-r-*-*-*-120-*-*-*-*-iso8859-1',
              stateBox=OFF,
              statePosition=(13, 12),
              stateTextColor='White',
              title=OFF,
              titleBackgroundColor='White',
              titleBackgroundStyle=MATCH,
              titleBox=OFF,
              titleFont='-*-verdana-medium-r-*-*-*-120-*-*-*-*-iso8859-1',
              titlePosition=(13, 20),
              titleTextColor='White',
              triad=OFF,
              triadColor='White',
              triadFont='-*-verdana-bold-r-normal--25-*',
              triadLabels=NUMBERS,
              triadPosition=(6, 12),
              triadSize=4)
session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(numericForm=REAL)

# open Database
# openMdb(pathName='')
os.chdir(WORK_PATH)

if EXECUTE_SCRIPT:
    print('EXECUTING', PATH_TO_SCRIPT)
    execfile(PATH_TO_SCRIPT)

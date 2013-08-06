#!/usr/bin/python
""" 
Generates the tr file based on the defined pyQt Project File
""" 

import os, sys
import subprocess

PLYPATH = "C:\Python27\Lib\site-packages\PyQt4\pylupdate4.exe"
LREPATH = "C:\Python27\Lib\site-packages\PyQt4\lrelease.exe"

FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

FILES = ("..\dxf2gcode_pyQt4_ui\dxf2gcode_pyQt4_ui.ui",
         "..\Core\ArcGeo.py",
         "..\Core\Config.py",
         "..\Core\Logger.py",
         "..\Core\Shape.py",
         "..\DXFImport\Import.py",
         "..\Gui\myCanvasClass.py",
         "..\PostPro\PostProcessor.py",
         "..\PostPro\PostProcessorConfig.py",
         "..\PostPro\TspOptimisation.py",
         "..\dxf2gcode.py")


TSFILES=("dxf2gcode_de_DE.ts",
        "dxf2gcode_fr.ts")


FILESSTR=""
for FILE in FILES:
    FILESSTR+=("%s\i18n\%s " %(FILEPATH, FILE))
    
TSFILESTR=""
for TSFILE in TSFILES:
    TSFILESTR+=("%s\i18n\%s " %(FILEPATH, TSFILE))

OPTIONS = ("-ts")

CMD1 = ("%s %s %s %s" % (PLYPATH, FILESSTR, OPTIONS, TSFILESTR))
print CMD1

RETCODE = subprocess.call(CMD1,shell=True)

CMD2 =("%s %s" %(LREPATH,TSFILESTR))
print CMD2

RETCODE = subprocess.call(CMD2,shell=True)


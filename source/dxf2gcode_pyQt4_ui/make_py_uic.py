#!/usr/bin/python
""" 
Generates the python file based on the defined uifile
""" 

import os, sys
import subprocess

PYT = "C:/Python27/pythonw.exe"


UICPATH = "C:\Python27\Lib\site-packages\PyQt4"
FILEPATH = os.path.realpath(os.path.dirname(sys.argv[0]))

UIFILE = "dxf2gcode_pyQt4_ui.ui"
PYFILE = "dxf2gcode_pyQt4_ui.py"

RCFILE = "dxf2gcode_images.qrc"
RCPYFILE = "dxf2gcode_images_rc.py"

OPTIONS = ("-o")

CMD1 = ("%s\pyuic4.bat %s %s %s" % (UICPATH, UIFILE, OPTIONS, PYFILE))
CMD2 = ("%s\pyrcc4.exe %s %s %s" % (UICPATH, OPTIONS, RCPYFILE, RCFILE))

print CMD1
RETCODE = subprocess.call(CMD1)

print CMD2
RETCODE = subprocess.call(CMD2)
#!/usr/bin/python

import os, sys
import subprocess

pyt = "C:/Python26/pythonw.exe"

uicpfad = "C:\Python26\Lib\site-packages\PyQt4\uic"
filepfad= os.path.realpath(os.path.dirname(sys.argv[0]))

uifile = "mein_test.ui"
ergfile= "mein_test.py"


options=("-o")
#print options


cmd=("%s %s\pyuic.py %s %s %s" %(pyt,uicpfad,uifile,options,ergfile))
print cmd
retcode=subprocess.call(cmd)

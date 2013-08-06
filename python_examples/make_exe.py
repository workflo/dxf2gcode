#!/usr/bin/python

import os, sys
import subprocess

pyinpfad = "D:\pyinstaller"
exemakepfad = "D:/dxf2gcode_exe_tkinter"
pyt = "C:/Python25/pythonw.exe"
filepfad= os.path.realpath(os.path.dirname(sys.argv[0]))
icon= ""
file = "NURBS_fitting_by_Biarc_curves_wx"


options=("--onefile --noconsol --upx --tk --icon=%s" %icon)
print options

#Verzwichniss wechseln
exemakepfad = unicode( exemakepfad, "utf-8" )
os.chdir(exemakepfad.encode( "utf-8" ))


cmd=("%s %s\Makespec.py %s %s/%s.py" %(pyt,pyinpfad,options,filepfad,file))
print cmd
retcode=subprocess.call(cmd)

cmd=("%s %s\Build.py %s\%s.spec" %(pyt,pyinpfad,exemakepfad,file))
print cmd
retcode=subprocess.call(cmd)

print "\n!!!!!!!Bitmaps und Languagues Ordner nicht vergessen!!!!!!"
print "\nFertig"
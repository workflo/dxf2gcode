#!/usr/bin/python

import os, sys
import subprocess

pyinpfad = "C:\Python26\pyinstaller-1.4"

pyt = "C:/Python26/pythonw.exe"
filepfad= os.path.realpath(os.path.dirname(sys.argv[0]))
exemakepfad=filepfad
file = "Starte_mein_gui"
icon= "%s/DXF2GCODE-001.ico" %filepfad

#options=("--onefile --noconsole --upx --icon=%s" %icon)
options=("--onefile --noconsole --upx")
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
# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'D:\\Eclipse_Workspace\\DXF2GCODE\\trunk\\python_examples\\qt/Starte_mein_gui.py'],
             pathex=['D:\\Eclipse_Workspace\\DXF2GCODE\\trunk\\python_examples\\qt'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'Starte_mein_gui.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False )

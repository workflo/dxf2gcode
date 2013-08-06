# -*- mode: python -*-
a = Analysis(['D:\\MyWorkspace\\DXF2GCODE\\trunk\\source/dxf2gcode.py'],
             pathex=['D:\\MyWorkspace\\DXF2GCODE\\trunk\\source'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\dxf2gcode', 'dxf2gcode.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='D:\\MyWorkspace\\DXF2GCODE\\trunk\\source\\DXF2GCODE-001.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'dxf2gcode'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'dxf2gcode.app'))

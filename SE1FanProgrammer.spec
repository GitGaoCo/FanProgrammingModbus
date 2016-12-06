# -*- mode: python -*-

block_cipher = None


a = Analysis(['SE1FanProgrammer.pyw'],
             pathex=['C:\\Users\\sesa137059\\Desktop\\SE1FanProgrammer'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

a.datas += [('Fan3Tests.csv', 'Fan3Tests.csv', 'DATA'),
            ('Fan2Tests.csv', 'Fan2Tests.csv', 'DATA'),
            ('Fan1Tests.csv', 'Fan1Tests.csv', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SE1FanProgrammer',
          debug=False,
          strip=False,
          upx=False,
          console=False , icon='.\\images\\fan.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='SE1FanProgrammer')

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['yamm.py'],
             pathex=['C:\\Users\\pineb\\Desktop\\python\\YetAnotherMediaManager'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
             
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          #[('v', None, 'OPTION')],
          name='yamm',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )

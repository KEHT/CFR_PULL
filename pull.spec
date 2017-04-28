# -*- mode: python -*-

block_cipher = None


a = Analysis(['pull.py'],
             pathex=['C:\\Users\\sjohnson\\Documents\\GitHub\\CFR_PULL'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='pull',
          debug=False,
          strip=False,
          upx=True,
          console=True )

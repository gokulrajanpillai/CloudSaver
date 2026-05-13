# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['cloudsaver/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('web', 'web'),
        ('cloudsaver/VERSION', 'cloudsaver'),
    ],
    hiddenimports=['PIL', 'sqlite3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CloudSaver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='packaging/macos/entitlements.plist',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CloudSaver',
)

app = BUNDLE(
    coll,
    name='CloudSaver.app',
    icon='packaging/macos/icon.icns',
    bundle_identifier='app.cloudsaver.desktop',
    version=open('cloudsaver/VERSION').read().strip(),
)

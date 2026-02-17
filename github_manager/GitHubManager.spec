# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for GitHub Manager
# Build: cd github_manager && pyinstaller GitHubManager.spec
# Icon: chạy python build_icon.py trước để tạo assets/icon.ico

import os
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
ICON_PATH = os.path.join(SPEC_DIR, 'assets', 'icon.ico')

a = Analysis(
    ['app.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=[(ICON_PATH, 'assets')] if os.path.isfile(ICON_PATH) else [],
    hiddenimports=['version'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GitHubManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH if os.path.isfile(ICON_PATH) else None,
)

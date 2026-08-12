# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the EchoDesk Desktop Controller.

Build with: pyinstaller EchoDeskController.spec
See docs/BUILD_GUIDE.md for the full explanation of every section below.
"""

import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = []
datas += [(".env.example", ".")]
datas += collect_data_files("pyqtgraph")
datas += collect_data_files("PySide6", subdir="Qt/plugins/platforms")
datas += collect_data_files("PySide6", subdir="Qt/plugins/imageformats")

hiddenimports = []
hiddenimports += collect_submodules("socketio")
hiddenimports += collect_submodules("engineio")
hiddenimports += ["platformdirs"]  # pulled in by pkg_resources' runtime hook, not visible to static analysis
if sys.platform == "win32":
    hiddenimports += ["win32timezone"]  # commonly missed by pywin32's own hook

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="EchoDeskController",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="app/assets/icon.ico",
    version="version_info.txt",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="EchoDeskController",
)

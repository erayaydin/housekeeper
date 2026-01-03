# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Housekeeper."""

import sys
from pathlib import Path

block_cipher = None

# Determine platform-specific settings
is_windows = sys.platform == "win32"
is_macos = sys.platform == "darwin"

# Hidden imports needed for the application
hiddenimports = [
    "plyer.platforms.linux.notification",
    "plyer.platforms.macosx.notification",
    "plyer.platforms.win.notification",
    "platformdirs",
    "watchdog.observers",
    "watchdog.events",
]

# Add platform-specific hidden imports
if is_windows:
    hiddenimports.extend([
        "win32serviceutil",
        "win32service",
        "win32event",
        "servicemanager",
        "housekeeper.daemon.windows",
    ])
else:
    hiddenimports.extend([
        "daemon",
        "daemon.pidfile",
        "housekeeper.daemon.unix",
        "housekeeper.daemon.runner",
    ])

a = Analysis(
    ["src/housekeeper/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="housekeeper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
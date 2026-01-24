# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CloudSim Desktop
Builds a standalone Windows executable
"""

import sys
from pathlib import Path

block_cipher = None

# Project root directory
project_root = Path('.').absolute()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include all UI modules
        ('ui', 'ui'),
        ('services', 'services'),
        ('models', 'models'),
        ('utils', 'utils'),
        # Logo and icon files
        ('logo.png', '.'),
        ('icon.png', '.'),
        ('icon.ico', '.'),
        # Documentation (optional, for reference)
        ('*.md', '.'),
    ],
    hiddenimports=[
        # PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # CloudSim modules
        'ui.main_window',
        'ui.sidebar',
        'ui.views.dashboard_view',
        'ui.views.compute_view',
        'ui.views.storage_view',
        'ui.views.database_view',
        'ui.views.serverless_view',
        'services.compute_service',
        'services.storage_service',
        'services.database_service',
        'services.serverless_service',
        'models.instance',
        'models.bucket',
        'models.database',
        'models.function',
        'utils.storage',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'unittest',
        'test',
        'tests',
    ],
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
    name='CloudSim',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window - GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # CloudSim logo as application icon
    onefile=True,  # Single executable file
)

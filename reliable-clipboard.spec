# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/reliable_clipboard/*.py', 'reliable_clipboard'),
        ('src/reliable_clipboard/assets/*.png', 'assets'),
    ],
    hiddenimports=[
        'reliable_clipboard',
        'reliable_clipboard.clip_history',
        'reliable_clipboard.clipboard_monitor',
        'reliable_clipboard.storage',
        'reliable_clipboard.gui',
        'reliable_clipboard.cli',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'pyperclip',
        'pyperclip.clipboards',
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        'sqlite3',
        'logging',
        'threading',
        'time',
        'datetime',
        'pathlib',
        'argparse',
    ],
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
    name='reliable-clipboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed mode - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

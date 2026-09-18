# -*- mode: python ; coding: utf-8 -*-

block_cipher = []

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('models', 'models'),
    ],
    hiddenimports=[
        'demucs',
        'whisperx',
        'faster_whisper',
        'torchcrepe',
        'torchaudio',
        'sounddevice',
        'soundfile',
        'librosa',
        'pydub',
        'scipy',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython'],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KaraokeForge',
    icon='assets/icon.ico',
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='KaraokeForge',
)

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Compass Python backend.
#
# Build (from the repo root):
#   .venv\Scripts\python.exe -m PyInstaller --clean --noconfirm backend\compass_backend.spec
#
# Produces a onedir bundle at backend/dist/Compass Backend/ containing
# Compass Backend.exe plus its _internal folder. onedir (instead of onefile)
# avoids the multi-hundred-MB self-extraction on every launch and is far more
# reliable for apps of this size.

import os

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

spec_dir = os.path.abspath(SPECPATH)
src_dir = os.path.join(spec_dir, 'src')
icon_path = os.path.abspath(os.path.join(spec_dir, '..', 'resources', 'compass.ico'))

# Bundle the compass package's data files (prompts, configs, RAG database
# seed, section tables) next to the executable under _internal/compass.
# Excludes: bytecode caches and the YOLO model weights - icon detection via
# torch/ultralytics is intentionally not part of the packaged app.
compass_data = Tree(
    os.path.join(src_dir, 'compass'),
    prefix='compass',
    excludes=['__pycache__', '*.pyc', '*.pt', '*.pth', '*.safetensors'],
)

a = Analysis(
    [os.path.join(src_dir, 'compass', 'app.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        # eventlet / socket.io async plumbing (imported dynamically)
        'eventlet.hubs.epolls',
        'eventlet.hubs.kqueue',
        'eventlet.hubs.selects',
        'eventlet.hubs.poll',
        'eventlet.hubs.hub',
        'engineio.async_drivers.eventlet',
        'flask_socketio',
        'socketio',
        'socketio.server',
        # dns (used by eventlet unless greendns disabled; keep for safety)
        'dns',
        'dns.resolver',
        'dns.asyncquery',
        'dns.asyncresolver',
        'dns.asyncbackend',
        'dns.versioned',
        'dns.rdtypes',
        # compass modules referenced via config strings / dynamic imports
        'compass.config.config',
        'compass.agent.agent',
        'compass.services.state_manager',
        'compass.services.workflow_manager',
        'compass.utils.utility',
        'compass.training_agent.training_agent',
    ] + collect_submodules('chromadb'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Heavy ML stack: only used by the optional YOLO icon detector and
        # experimental captioners, all of which degrade gracefully when
        # missing (see training_agent.py). Excluding keeps the bundle small.
        'torch',
        'torchvision',
        'torchaudio',
        'ultralytics',
        'easyocr',
        'transformers',
        'sklearn',
        'scipy',
        'matplotlib',
        # Not used by the backend at runtime
        'gevent',
        'IPython',
        'jupyter',
        'pytest',
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
    [],
    exclude_binaries=True,
    name='Compass Backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    compass_data,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Compass Backend',
)

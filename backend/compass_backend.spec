# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules


block_cipher = None


a = Analysis(
    ['src\\compass\\app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('src/compass', 'compass'),
        # Add data files for torch and easyocr
    ],
    hiddenimports=[
        'eventlet.hubs.epolls', 
        'eventlet.hubs.kqueue', 
        'eventlet.hubs.selects', 
        'engineio.async_drivers.eventlet', 
        'flask_socketio', 
        'eventlet.hubs.poll', 
        'eventlet.hubs.hub', 
        'socketio', 
        'socketio.server', 
        'compass.config.config', 
        'compass.agent.agent', 
        'compass.services.state_manager', 
        'compass.utils.utility', 
        'compass.training_agent.training_agent', 
        'compass.services.workflow_manager',
        # Add torch and easyocr related imports
        'torch',
        'torch._C',
        # 'torch._numpy._ufuncs',
        'torch.nn',
        'torch.nn.functional',
        'torch.nn.modules',
        'torch.nn.parallel',
        'torch.utils.data',
        'torchvision',
        'torchvision.transforms',
        'torchvision.models',
        'torchvision.ops',
        'easyocr',
        'easyocr.recognition',
        'easyocr.detection',
        'easyocr.utils',
        'PIL',
        'cv2',
        'numpy',
        'inspect',  # Added to help with inspect module errors
        # Add scipy modules
        'scipy',
        'scipy.ndimage',
        'scipy._lib',
        'scipy._lib.array_api_compat',
        'scipy._lib.array_api_compat.numpy',
        'scipy._lib.array_api_compat.numpy.fft',
        'scipy.ndimage._support_alternative_backends',
        # Add DNS modules that were previously excluded
        'dns',
        'dns.resolver',
        'dns.asyncquery',
        'dns.asyncresolver',
        'dns.asyncbackend',
        'dns.versioned',
        'dns.rdtypes',
        'tokenizers',
        # FIX for chromadb missing ONNX model
        'chromadb.utils.embedding_functions.onnx',
        #'chromadb.utils.embedding_functions.onnx.ONNXMiniLM_L6_V2',
     ] + collect_submodules('chromadb'),
    hookspath=[],  # Removed custom hooks path
    hooksconfig={},
    runtime_hooks=[],  # Removed runtime hooks
    excludes=[
        'transformers',
        'torch._numpy',  # <- Exclude the entire torch._numpy module
        'torch._numpy._ufuncs',  # Exclude the problematic module
        'torch._dynamo',  # Exclude torch dynamo which uses the ufuncs module
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
    name='compass_backend',
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
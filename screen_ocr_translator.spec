# PyInstaller spec for Screen OCR Translator.
#
# Build (from an environment that has the app's dependencies + pyinstaller):
#     pyinstaller screen_ocr_translator.spec
#
# Produces a one-folder app in dist/ScreenOCRTranslator/ (onedir, not onefile —
# onefile is unreliable and slow to start with a package as large as PyTorch).
#
# NOTE ON SIZE: the bundle includes PyTorch. With the CPU build it is roughly
# 600-800 MB; with the CUDA (GPU) build it is ~3.5 GB and will exceed GitHub's
# 2 GB per-file release-asset limit. Build in a clean venv with CPU-only torch
# if you intend to publish it. See the README's "Building a standalone .exe".

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for pkg in ['easyocr', 'torch', 'torchvision', 'skimage', 'scipy', 'deep_translator']:
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScreenOCRTranslator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # GUI app: no console window. Set True to see tracebacks.
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ScreenOCRTranslator',
)

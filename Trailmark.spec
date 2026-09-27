# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['point_logger.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('templates', 'templates')],
    # 'sounddevice' is added explicitly even though point_logger.py imports
    # asr.py at module level (so PyInstaller's bytecode scan should already
    # walk into asr.py's function-local `import sounddevice as sd` calls and
    # discover it that way) — those imports sit inside try/except ImportError
    # blocks, which is exactly the pattern that can make an import scanner
    # treat the dependency as optional/best-effort rather than pulling in its
    # hook. Listing it here forces PyInstaller's first-party sounddevice hook
    # to run, which is what actually collects the bundled PortAudio binary.
    # 'onnxruntime' and 'numpy' for the same reason: speaker.py imports both
    # inside functions, behind speaker.available()'s try/except, and the
    # contrib onnxruntime hook is what collects its provider DLLs.
    hiddenimports=['webview.platforms.winforms', 'sounddevice', 'onnxruntime', 'numpy'],
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
    a.datas,
    [],
    name='Trailmark',
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
    icon=['app.ico'],
)

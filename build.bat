@echo off
cd /d "%~dp0"
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name Trailmark --icon app.ico ^
  --add-data "assets;assets" ^
  --add-data "templates;templates" ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import sounddevice --hidden-import onnxruntime --hidden-import numpy ^
  point_logger.py
echo.
echo Binary: dist\Trailmark.exe
pause
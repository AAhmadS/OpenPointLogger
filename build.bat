@echo off
cd /d "%~dp0"
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name Trailmark --icon app.ico ^
  --add-data "assets;assets" ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import pystray._win32 ^
  point_logger.py
echo.
echo Binary: dist\Trailmark.exe
pause
@echo off
title OpenPointLogger - Pin to taskbar
echo.
echo  Pinning OpenPointLogger to the taskbar...
echo.
set "PINDIR=%APPDATA%\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
set "LNK=%USERPROFILE%\Desktop\OpenPointLogger.lnk"

if not exist "%LNK%" (
  echo  Desktop shortcut not found. Creating it...
  powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut('%LNK%');$s.TargetPath='%LOCALAPPDATA%\Programs\OpenPointLogger\OpenPointLogger.exe';$s.WorkingDirectory='%LOCALAPPDATA%\Programs\OpenPointLogger';$s.IconLocation='%LOCALAPPDATA%\Programs\OpenPointLogger\app.ico,0';$s.Save()"
)

mkdir "%PINDIR%" 2>nul
copy /Y "%LNK%" "%PINDIR%\OpenPointLogger.lnk" >nul

rem Refresh the shell so the taskbar re-reads the pinned list
taskkill /f /im explorer.exe >nul 2>&1
start "" explorer.exe
timeout /t 3 /nobreak >nul

echo.
echo  If OpenPointLogger does not appear pinned on the taskbar, do it by hand:
echo    1. Find the OpenPointLogger shortcut on your Desktop
echo    2. Drag it onto the taskbar and drop it there.
echo.
pause
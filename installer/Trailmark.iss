; Trailmark installer (Inno Setup 6). Per-user, no admin: installs into
; %LOCALAPPDATA%\Programs\Trailmark, the layout the app already runs from.
; Data (points, config, attachments, exports) lives in %APPDATA%\Trailmark
; and is created by the app itself - the installer never touches it, so
; installing over an existing copy cannot lose anything.
;
; Build:  iscc installer\Trailmark.iss   (from the repo root, after the
;         PyInstaller build, so dist\Trailmark.exe is the seed binary)
; Output: installer\Output\Trailmark-Setup-<version>.exe
;
; AppId is stable forever: changing it orphans the uninstall entry and
; breaks upgrades. Version comes from AppVersion below - keep it in step
; with the release tag.

#define AppVersion "0.1.0"
#define AppVerName "Trailmark 0.1.0 (seed 1)"

[Setup]
AppId={{47A0AA64-B05F-41E2-AD11-9D7A30792357}
AppName=Trailmark
AppVersion={#AppVersion}
AppVerName={#AppVerName}
AppPublisher=Chantex
AppPublisherURL=https://trailmark.chantex.ir
DefaultDirName={localappdata}\Programs\Trailmark
DisableDirPage=no
DefaultGroupName=Trailmark
DisableProgramGroupPage=no
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Trailmark-Setup-{#AppVersion}
SetupIconFile=..\app.ico
UninstallDisplayIcon={app}\Trailmark.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#AppVersion}
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: desktopicon; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Trailmark.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Trailmark"; Filename: "{app}\Trailmark.exe"
Name: "{autodesktop}\Trailmark"; Filename: "{app}\Trailmark.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Trailmark.exe"; Description: "{cm:LaunchProgram,Trailmark}"; Flags: nowait postinstall skipifsilent

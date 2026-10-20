; Inno Setup 6 — instalador de GCISCAR (PC local, sin internet).
; Compilar: installer\build.py  (o: ISCC.exe installer\GCISCAR.iss)
; Instalacion por usuario, sin pedir administrador: %LOCALAPPDATA%\Programs\GCISCAR

#define MyAppName "GCISCAR"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "GCISCAR"
#define MyAppExeName "GCISCAR.exe"

[Setup]
AppId={{9B2C7E54-6D1A-4B8F-9C3E-5A7D2F41B6E8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=GCISCAR-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\GCISCAR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\GCISCAR"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\GCISCAR"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

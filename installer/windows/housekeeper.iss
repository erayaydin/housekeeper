; Inno Setup script for Housekeeper
; https://jrsoftware.org/isinfo.php

#define MyAppName "Housekeeper"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Housekeeper"
#define MyAppURL "https://github.com/erayaydin/housekeeper"
#define MyAppExeName "housekeeper.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=housekeeper-windows-amd64-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Add to PATH"; GroupDescription: "System integration:"
Name: "installservice"; Description: "Install as Windows service (starts automatically)"; GroupDescription: "System integration:"

[Files]
Source: "dist\housekeeper-windows-amd64.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "daemon install"; StatusMsg: "Installing Windows service..."; Tasks: installservice; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Parameters: "daemon start"; StatusMsg: "Starting Windows service..."; Tasks: installservice; Flags: runhidden

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "daemon stop"; StatusMsg: "Stopping Windows service..."; Flags: runhidden skipifdoesntexist
Filename: "{app}\{#MyAppExeName}"; Parameters: "daemon uninstall"; StatusMsg: "Uninstalling Windows service..."; Flags: runhidden skipifdoesntexist

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Path: string;
  AppDir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDir := ExpandConstant('{app}');
    if RegQueryStringValue(HKEY_LOCAL_MACHINE,
      'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
      'Path', Path) then
    begin
      if Pos(';' + AppDir, Path) > 0 then
      begin
        StringChangeEx(Path, ';' + AppDir, '', True);
        RegWriteStringValue(HKEY_LOCAL_MACHINE,
          'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
          'Path', Path);
      end;
    end;
  end;
end;
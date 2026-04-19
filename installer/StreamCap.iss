#define MyAppName "StreamCap"
#define MyAppPublisher "StreamCap"
#define MyAppExeName "StreamCap.exe"
#define MyBuildDir "..\dist\main_qt.dist"
#define MyAppVersion GetVersionNumbersString(MyBuildDir + "\" + MyAppExeName)

[Setup]
AppId={{8F9A3E6B-6E7D-4BC8-9F67-5A4B7F91F6C2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
SetupIconFile=StreamCapInstaller.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
OutputDir=..\dist\installer
OutputBaseFilename=StreamCapSetup-{#MyAppVersion}
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "config\user_settings.json,config\cookies.json,config\accounts.json,config\web_auth.json,config\recordings.db,config\recordings.db-*,config\recordings.json,config\*.bak"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DeleteUserData: Boolean;

function InitializeUninstall(): Boolean;
begin
  DeleteUserData := MsgBox(
    'Do you also want to delete StreamCap user data?' + #13#10 + #13#10 +
    'This removes configuration, cookies, accounts, authentication data, and recordings.db from:' + #13#10 +
    ExpandConstant('{localappdata}\StreamCap'),
    mbConfirmation,
    MB_YESNO
  ) = IDYES;

  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and DeleteUserData then
  begin
    DelTree(ExpandConstant('{localappdata}\StreamCap'), True, True, True);
  end;
end;

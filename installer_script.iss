[Setup]
AppName=Offline Attendance System
AppVersion=1.0
AppPublisher=Your Organization
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={autopf}\OfflineAttendanceSystem
DisableProgramGroupPage=yes
LicenseFile=
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=OfflineAttendanceSystem_Setup
SetupIconFile=static\images\ccs.png
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\attendance_system.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\Offline Attendance System"; Filename: "{app}\attendance_system.exe"
Name: "{autodesktop}\Offline Attendance System"; Filename: "{app}\attendance_system.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\attendance_system.exe"; Description: "{cm:LaunchProgram,Offline Attendance System}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('Installation completed successfully!' + #13#10 + 
           'The application will start automatically on port 5000.' + #13#10 +
           'Access it via your browser at http://localhost:5000', 
           mbInformation, MB_OK);
  end;
end;

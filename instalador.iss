[Setup]
AppName=ConstruSeco Pereyra
AppVersion=1.0
DefaultDirName=C:\ConstruSecoPereyra
DefaultGroupName=ConstruSeco Pereyra
DisableProgramGroupPage=yes
OutputDir=instalador_salida
OutputBaseFilename=Instalador_ConstruSecoPereyra
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\ConstruSecoPereyra\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\ConstruSeco Pereyra"; Filename: "{app}\ConstruSecoPereyra.exe"
Name: "{group}\ConstruSeco Pereyra"; Filename: "{app}\ConstruSecoPereyra.exe"

[Run]
Filename: "{app}\ConstruSecoPereyra.exe"; Description: "Abrir ConstruSeco Pereyra"; Flags: nowait postinstall skipifsilent
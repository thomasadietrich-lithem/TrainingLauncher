; Installeur NeuroVision Solidaire (Inno Setup 6) — document directeur, chapitre 16.2 / 16.6.
;
; INVARIANTS (ne JAMAIS changer, sinon les installeurs futurs — signés — ne mettront plus à jour les postes) :
;   AppId            {6F9149E1-9C18-49E3-B14B-34AF00CD0987}
;   DefaultDirName   {localappdata}\NeuroVisionSolidaire\app
;   installation par utilisateur, sans droits administrateur.
; Les dossiers exercices\ et donnees\ (à côté de app\) appartiennent au lanceur : l'installeur ne les crée ni ne les
; efface, la désinstallation non plus (les séances du patient sont conservées).
;
; Compilation (CI) : iscc /DAppVersion=1.0.0 /DSourceDir=..\dist\NeuroVision installeur\NeuroVision.iss
; Mode silencieux (auto-mise à jour par le lanceur) : Installer_NeuroVision.exe /VERYSILENT /SUPPRESSMSGBOXES
;   /NORESTART /RELANCER=1   → relance NeuroVision à la fin.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\NeuroVision"
#endif

[Setup]
AppId={{6F9149E1-9C18-49E3-B14B-34AF00CD0987}
AppName=NeuroVision Solidaire
AppVersion={#AppVersion}
AppVerName=NeuroVision Solidaire {#AppVersion}
AppPublisher=NeuroVision Solidaire
VersionInfoVersion={#AppVersion}
DefaultDirName={localappdata}\NeuroVisionSolidaire\app
DisableDirPage=yes
DisableProgramGroupPage=yes
DefaultGroupName=NeuroVision Solidaire
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\sortie
OutputBaseFilename=Installer_NeuroVision
SetupIconFile=neurovision.ico
UninstallDisplayIcon={app}\NeuroVision.exe
UninstallDisplayName=NeuroVision Solidaire
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no
ShowLanguageDialog=auto

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
fr.Lancer=Lancer NeuroVision maintenant
en.Lancer=Start NeuroVision now

[Files]
; Remplacement complet du lanceur à chaque version (ignoreversion), sans toucher au reste.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; anciens fichiers du lanceur uniquement (jamais exercices\ ni donnees\, qui sont hors de {app})
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{userdesktop}\NeuroVision Solidaire"; Filename: "{app}\NeuroVision.exe"; IconFilename: "{app}\NeuroVision.exe"
Name: "{userprograms}\NeuroVision Solidaire"; Filename: "{app}\NeuroVision.exe"; IconFilename: "{app}\NeuroVision.exe"

[Run]
; installation normale : case « Lancer NeuroVision maintenant » sur la dernière page
Filename: "{app}\NeuroVision.exe"; Description: "{cm:Lancer}"; Flags: nowait postinstall skipifsilent
; auto-mise à jour silencieuse demandée par le lanceur : relance automatique
Filename: "{app}\NeuroVision.exe"; Flags: nowait; Check: RelancerDemande

[Code]
function RelancerDemande(): Boolean;
begin
  Result := WizardSilent() and (ExpandConstant('{param:RELANCER|0}') = '1');
end;

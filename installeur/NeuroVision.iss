; Installeur NeuroVision Solidaire (Inno Setup 6) — document directeur, chapitre 16.2 / 16.6.
;
; INVARIANTS (ne JAMAIS changer, sinon les installeurs futurs — signés — ne mettront plus à jour les postes) :
;   AppId            {6F9149E1-9C18-49E3-B14B-34AF00CD0987}
;   DefaultDirName   {localappdata}\NeuroVisionSolidaire\app
;   installation par utilisateur, sans droits administrateur.
; Les dossiers exercices\ (à côté de app\) et le dossier de DONNÉES choisi au 1er lancement (par défaut
; Documents\NeuroVision Solidaire) ne sont ni créés ni effacés par l'installeur ou la désinstallation ; un message
; le rappelle avant de désinstaller.
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
fr.AvertDesinst=Vos séances et vos réglages ne sont PAS supprimés : ils restent dans le dossier choisi au premier lancement (par défaut « Documents\NeuroVision Solidaire »).%n%nNe supprimez pas ce dossier : les séances qui n'ont pas encore été envoyées à l'association s'y trouvent.%n%nContinuer la désinstallation ?
en.AvertDesinst=Your sessions and settings are NOT deleted: they stay in the folder chosen at first start (by default "Documents\NeuroVision Solidaire").%n%nDo not delete this folder: sessions not yet sent to the association are kept there.%n%nContinue uninstalling?

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
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if not UninstallSilent() then
    Result := MsgBox(CustomMessage('AvertDesinst'), mbConfirmation, MB_YESNO) = IDYES;
end;

function RelancerDemande(): Boolean;
begin
  Result := WizardSilent() and (ExpandConstant('{param:RELANCER|0}') = '1');
end;

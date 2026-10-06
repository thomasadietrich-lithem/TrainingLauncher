@echo off
REM ---------------------------------------------------------------------------
REM Creation des cles de signature NeuroVision (a faire UNE seule fois).
REM
REM Cree deux cles : "principale" (servira a publier) et "secours" (a garder
REM hors ligne, en cas de perte ou de vol de la principale).
REM Les cles PRIVEES sont ecrites dans le dossier que vous indiquez (de
REM preference une cle USB). Elles ne doivent jamais etre envoyees a qui que
REM ce soit, ni a Claude, ni sur AWS.
REM Les cles PUBLIQUES s'affichent a la fin : copiez-les et collez-les a Claude.
REM ---------------------------------------------------------------------------
chcp 65001 >nul
cd /d "%~dp0\.."

set PY=python
where py >nul 2>nul && set PY=py

echo.
set /p SORTIE=Dossier ou ecrire les cles privees (ex. E:\cles_NVS) :
if "%SORTIE%"=="" goto :fin

echo.
echo Installation du module de cryptographie (si necessaire)...
%PY% -m pip install --user --quiet cryptography

%PY% outils\generer_cles.py principale --sortie "%SORTIE%" || goto :erreur
%PY% outils\generer_cles.py secours --sortie "%SORTIE%" || goto :erreur

echo.
echo ===========================================================================
echo  TERMINE. Copiez tout le texte ci-dessous et collez-le a Claude :
echo ===========================================================================
type nvs_lanceur\cles_publiques.json
echo ===========================================================================
echo.
echo  Cles privees : "%SORTIE%"  (principale.cle_privee et secours.cle_privee)
echo  Gardez secours.cle_privee HORS LIGNE (cle USB rangee).
goto :fin

:erreur
echo.
echo  ERREUR : les cles n'ont pas ete creees. Copiez ce message a Claude.

:fin
echo.
pause

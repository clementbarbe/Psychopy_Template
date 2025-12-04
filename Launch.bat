@echo off

REM Activation de l’environnement conda via Miniforge
call "C:\ProgramData\miniforge3\Scripts\conda.bat" activate ton_env

REM Aller dans le dossier du projet
cd /d "C:\chemin\vers\ton\projet"

REM Exécuter le script Python
python main.py

pause

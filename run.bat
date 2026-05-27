@echo off
REM Starte die Streamlit App mit automatischer Dependency-Installation
REM Doppelklick zum Ausführen

cd /d "%~dp0"
python setup_and_run.py
pause

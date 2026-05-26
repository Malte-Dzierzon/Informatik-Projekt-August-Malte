@echo off
REM Starte die Streamlit App für Neuronales Netzwerk
REM Doppelklick zum Ausführen

cd /d "%~dp0"
C:\Users\malte\.local\bin\python3.14.exe -m streamlit run app.py
pause

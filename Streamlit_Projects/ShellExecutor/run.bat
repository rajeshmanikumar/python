@echo off
title ShellExecutor Pro
echo Starting ShellExecutor Pro Web Application...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)
pause

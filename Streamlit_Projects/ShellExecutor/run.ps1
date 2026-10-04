Write-Host "Starting ShellExecutor Pro Web Application..." -ForegroundColor Cyan
if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m streamlit run app.py
} else {
    python -m streamlit run app.py
}

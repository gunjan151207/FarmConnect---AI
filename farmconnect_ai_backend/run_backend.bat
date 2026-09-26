@echo off
cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
)

echo Starting FarmConnect AI backend...
echo Interactive API Documentation: http://127.0.0.1:8000/docs
echo.

py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 || python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause


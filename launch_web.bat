@echo off
REM Windows launcher for Nunalleq OCR Web Interface
REM Double-click this file to start the web application

echo ======================================================
echo   Nunalleq Artifact Photo Organizer - Web Interface
echo ======================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.9 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check if nunalleq-ocr is installed
python -c "import nunalleq_ocr" >nul 2>&1
if errorlevel 1 (
    echo Installing nunalleq-ocr...
    python -m pip install -e ".[gui]"
    if errorlevel 1 (
        echo Installation failed. Please check the error messages above.
        pause
        exit /b 1
    )
) else (
    REM Check if Flask is installed
    python -c "import flask" >nul 2>&1
    if errorlevel 1 (
        echo Installing web interface dependencies...
        python -m pip install -e ".[gui]"
    )
)

REM Launch the web interface
echo.
echo Starting web interface...
echo Your web browser will open automatically.
echo.
echo Press Ctrl+C to stop the server when you're done.
echo.

python -m nunalleq_ocr.webapp.app

pause

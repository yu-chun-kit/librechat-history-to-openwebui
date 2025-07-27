@echo off
setlocal

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    exit /b 1
)

REM Check for command
if "%1"=="" (
    echo Usage: run.bat [migrate^|presets^|gui^|backup]
    exit /b 1
)

if "%1"=="migrate" (
    echo Running conversation migration...
    python -m scripts.migrate_conversations
) else if "%1"=="presets" (
    echo Running preset generation...
    python -m scripts.generate_presets
) else if "%1"=="gui" (
    echo Starting GUI...
    python -m gui.app
) else if "%1"=="backup" (
    echo Running LibreChat backup...
    python -m scripts.backup_librechat
) else (
    echo Invalid command: %1
    echo Usage: run.bat [migrate^|presets^|gui^|backup]
    exit /b 1
)

endlocal
echo Done.

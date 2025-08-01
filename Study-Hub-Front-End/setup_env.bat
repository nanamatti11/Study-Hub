@echo off
echo Setting up Study Hub Environment...
echo ================================

:: Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python first.
    echo You can download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if virtual environment exists
if exist "Study-Hub-env" (
    echo Removing existing virtual environment...
    rmdir /s /q "Study-Hub-env"
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv Study-Hub-env

:: Activate virtual environment and install requirements
echo Activating virtual environment...
call .\Study-Hub-env\Scripts\activate.bat

:: Install requirements
echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ================================
echo Setup completed successfully!
echo.
echo To activate the environment in the future, run:
echo .\Study-Hub-env\Scripts\activate.bat
echo.
echo To deactivate the environment, simply type:
echo deactivate
echo.
echo Press any key to continue...
pause > nul 
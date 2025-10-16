@echo off
REM setup.bat - initialize budget analyzer project

echo 🏗️  setting up budget analyzer...

REM create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM install dependencies
pip install -r requirements.txt

REM create directory structure
mkdir data\output
mkdir logs

echo ✅ environment ready!
echo.
echo next steps:
echo   1. call venv\Scripts\activate.bat
echo   2. place your transactions.csv in data/
echo   3. python main.py

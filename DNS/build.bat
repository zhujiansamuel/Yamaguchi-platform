@echo off
echo ===================================
echo   DNS Config Tool - Build Script
echo ===================================
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Building executable...
pyinstaller --onefile --windowed ^
    --name "DNS設定ツール" ^
    --add-data "assets;assets" ^
    --icon=NONE ^
    main.py

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo ===================================
echo   Build complete!
echo   Output: dist\DNS設定ツール.exe
echo ===================================
pause

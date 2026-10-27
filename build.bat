@echo off
rem Build GPO.exe as a single file. Output: dist\GPO.exe
cd /d "%~dp0"
uv sync || exit /b 1
uv run pyinstaller GPO.spec --noconfirm --clean || exit /b 1
echo.
echo Done: %~dp0dist\GPO.exe

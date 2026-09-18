@echo off
rem Запуск веб-морды VIN-декодера на localhost:8777
cd /d "%~dp0"
start "" http://localhost:8777
python -m http.server 8777

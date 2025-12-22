@echo off
echo ==========================================
echo       Dungeon Crawler Launcher
echo ==========================================

echo [0/2] Cleaning up old processes...
taskkill /F /FI "WINDOWTITLE eq Dungeon Crawler Server" >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

echo [1/2] Starting Dungeon Crawler Server...
:: Start python in a new minimized window with a title
start "Dungeon Crawler Server" /MIN python app.py

echo Waiting for server to spin up...
timeout /t 3 /nobreak >nul

echo [2/2] Opening Web Browser...
start http://127.0.0.1:5000

echo.
echo Game is running! Check the minimized "Dungeon Crawler Server" window if you need to see logs.
echo To stop the game, close that window.
pause

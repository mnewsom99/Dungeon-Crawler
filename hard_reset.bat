@echo off
cd /d "c:\Users\mnews\OneDrive\Documents\AI_Projects\Dungeon-Crawler"
echo Killing all Python processes...
taskkill /F /IM python.exe /T 2>nul
echo.
echo Cleaning up temporary files...
if exist dungeon.db del dungeon.db
echo.
echo Starting Dungeon Crawler...
python app.py
pause

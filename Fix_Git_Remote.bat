@echo off
echo Fixing Git Remote URL to 'Dungeon-Crawler'...
git remote set-url origin https://github.com/mnewsom99/Dungeon-Crawler.git
echo.
echo New Remote Settings:
git remote -v
echo.
echo Use this script AFTER you have renamed the repository on GitHub.
pause

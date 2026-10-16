@echo off
title Velocity Korean - Video Generator
cd /d "%~dp0"

echo ============================================
echo   Velocity Korean - Video Generator
echo ============================================
echo.

echo [1] Long-form video
echo [2] Reels (short)
echo.
set /p MODE="Choose (1 or 2): "
echo.

if "%MODE%"=="2" (
    python facebook_reels_automation.py
    goto :end
)

set /p PHRASES="Number of phrases (default 60): "
if "%PHRASES%"=="" set PHRASES=60

set /p CATEGORY="Category (blank = random): "
echo.
if not "%CATEGORY%"=="" (
    python youtube_longform_automation.py --phrases %PHRASES% --category "%CATEGORY%"
) else (
    python youtube_longform_automation.py --phrases %PHRASES%
)

:end
echo.
echo Done!
pause

@echo off
title Clear directory logs...
echo Delete all LOGS...
timeout /t 3 /nobreak >nul

set "current=%~dp0"
set "me=%~nx0"

REM Delete all logs and no this bat fille
for %%f in ("%current%\*") do (
    if /I not "%%~nxf"=="%me%" del /q "%%~f"
)

REM Delete all pidpapku
for /d %%i in ("%current%\*") do rd /s /q "%%i"

echo Good! All logs - clear.
pause
